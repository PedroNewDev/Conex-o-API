import os
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from db import buscar_conversa_por_sessao, criar_conversa, inicializar_banco, inserir_mensagem
from prompts import MODOS, MODO_PADRAO, aplicar_tipo_prompt, escolher_provedor, rotear, FORCAS_PROVEDOR
from safety import validar_mensagem

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave-secreta-padrao")

GEMINI_MODEL    = "gemini-2.0-flash"
GROQ_MODEL      = "llama-3.3-70b-versatile"
CEREBRAS_MODEL  = "llama-3.3-70b"
GPT_MODEL       = "gpt-4o-mini"

_gemini = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

_groq = None
_groq_disponivel = False
if os.getenv("GROQ_API_KEY"):
    try:
        from langchain_groq import ChatGroq
        _groq = ChatGroq(model=GROQ_MODEL, api_key=os.getenv("GROQ_API_KEY"))
        _groq_disponivel = True
    except ImportError:
        pass

_cerebras = None
_cerebras_disponivel = False
if os.getenv("CEREBRAS_API_KEY"):
    try:
        from langchain_cerebras import ChatCerebras
        _cerebras = ChatCerebras(model=CEREBRAS_MODEL, api_key=os.getenv("CEREBRAS_API_KEY"))
        _cerebras_disponivel = True
    except ImportError:
        pass

_gpt = None
_gpt_disponivel = False
if os.getenv("OPENAI_API_KEY"):
    try:
        from langchain_openai import ChatOpenAI
        _gpt = ChatOpenAI(model=GPT_MODEL, api_key=os.getenv("OPENAI_API_KEY"))
        _gpt_disponivel = True
    except ImportError:
        pass

conversation_histories: dict[int, InMemoryChatMessageHistory] = {}

# Mapa nome → (objeto LLM, modelo) para despacho dinâmico pelo roteador
def _mapa_llms():
    m = {"gemini": (_gemini, GEMINI_MODEL)}
    if _groq_disponivel:     m["groq"] = (_groq, GROQ_MODEL)
    if _cerebras_disponivel: m["cerebras"] = (_cerebras, CEREBRAS_MODEL)
    if _gpt_disponivel:      m["gpt"] = (_gpt, GPT_MODEL)
    return m


def _provedores_ativos() -> set:
    return set(_mapa_llms().keys())


# IA-juíza: usa Groq se houver (latência baixa), senão Gemini
def _llm_juiz():
    return _groq if _groq_disponivel else _gemini

with app.app_context():
    inicializar_banco()


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc).upper()
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg or "QUOTA" in msg


def _invocar_llm(llm, mensagens):
    resp = llm.invoke(mensagens)
    tokens = resp.usage_metadata.get("total_tokens", 0) if resp.usage_metadata else 0
    return resp.content, tokens


def _montar_mensagens(history: InMemoryChatMessageHistory, sistema: str) -> list:
    return [SystemMessage(content=sistema)] + list(history.messages)


@app.route("/")
def index():
    if "sessao_id" not in session:
        session["sessao_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/status")
def status():
    return jsonify({
        "gemini": True,
        "groq": _groq_disponivel,
        "cerebras": _cerebras_disponivel,
        "gpt": _gpt_disponivel,
        "modos": list(MODOS.keys()),
        "tipos_prompt": ["simples", "estruturado", "especializado"],
    })


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    mensagem_original = data.get("mensagem", "").strip()
    modo = data.get("modo", MODO_PADRAO)
    tipo_prompt = data.get("tipo_prompt", "simples")

    if not mensagem_original:
        return jsonify({"erro": "Mensagem vazia"}), 400

    if modo not in MODOS:
        modo = MODO_PADRAO
    if tipo_prompt not in ("simples", "estruturado", "especializado"):
        tipo_prompt = "simples"

    seguro, motivo = validar_mensagem(mensagem_original)
    if not seguro:
        return jsonify({"erro": motivo, "bloqueado": True}), 400

    sessao_id = session.get("sessao_id", str(uuid.uuid4()))
    conversa_id = buscar_conversa_por_sessao(sessao_id)
    if not conversa_id:
        conversa_id = criar_conversa(sessao_id)

    inserir_mensagem(conversa_id, "usuario", mensagem_original)

    history = conversation_histories.setdefault(conversa_id, InMemoryChatMessageHistory())

    mensagem_enviada = aplicar_tipo_prompt(mensagem_original, tipo_prompt)
    history.add_user_message(mensagem_enviada)

    sistema = MODOS[modo]
    msgs = _montar_mensagens(history, sistema)

    # ── ROTEAMENTO INTELIGENTE (Nível 1 heurística + Nível 2 IA-juíza) ──
    rota = rotear(
        mensagem_original, modo,
        llm_juiz=_llm_juiz(),
        provedores_ativos=_provedores_ativos(),
    )
    provedor = rota["provedor"]
    etapas = rota["etapas"]

    mapa = _mapa_llms()
    fallback_aplicado = False

    try:
        if provedor == "ambos" and _groq_disponivel:
            resultado = _invocar_ambos(msgs, history, conversa_id, modo, tipo_prompt)
            resultado["roteamento"] = {
                "provedor": "ambos",
                "motivo": rota["motivo"],
                "etapas": etapas,
            }
            return jsonify(resultado)

        # Despacho dinâmico do provedor escolhido pelo roteador
        if provedor in mapa:
            llm, modelo_usado = mapa[provedor]
            try:
                conteudo, tokens = _invocar_llm(llm, msgs)
            except Exception as e:
                # Provedor escolhido falhou por cota → cadeia de fallback
                if _is_quota_error(e):
                    etapas = etapas + [f"{provedor.upper()} sem cota → fallback automático"]
                    conteudo, tokens, modelo_usado, provedor = _invocar_com_fallback(msgs)
                    fallback_aplicado = True
                else:
                    raise
        else:
            conteudo, tokens, modelo_usado, provedor = _invocar_com_fallback(msgs)
            fallback_aplicado = True

        if fallback_aplicado:
            etapas = etapas + [f"Resposta entregue por {provedor.upper()} (fallback)"]

    except Exception as e:
        if _is_quota_error(e):
            fallbacks = [n for n, ok in [("Groq", _groq_disponivel), ("Cerebras", _cerebras_disponivel), ("GPT", _gpt_disponivel)] if ok]
            sufixo = f" {' e '.join(fallbacks)} também falharam." if fallbacks else \
                     " Configure GROQ_API_KEY ou OPENAI_API_KEY para fallback automático."
            return jsonify({"erro": "Cota da API esgotada." + sufixo}), 429
        return jsonify({"erro": str(e)}), 500

    history.add_ai_message(conteudo)
    inserir_mensagem(conversa_id, "ia", conteudo, modelo=modelo_usado, tokens=tokens)

    return jsonify({
        "resposta": conteudo,
        "modelo": modelo_usado,
        "provedor": provedor,
        "modo": modo,
        "tipo_prompt": tipo_prompt,
        "tokens": tokens,
        "roteamento": {
            "provedor": provedor,
            "motivo": rota["motivo"],
            "etapas": etapas,
            "fallback": fallback_aplicado,
        },
    })


def _invocar_com_fallback(msgs):
    """Tenta Gemini → Groq → Cerebras → GPT em ordem, pulando quando quota esgota."""
    candidatos = [(_gemini, GEMINI_MODEL, "gemini")]
    if _groq_disponivel:
        candidatos.append((_groq, GROQ_MODEL, "groq"))
    if _cerebras_disponivel:
        candidatos.append((_cerebras, CEREBRAS_MODEL, "cerebras"))
    if _gpt_disponivel:
        candidatos.append((_gpt, GPT_MODEL, "gpt"))

    ultimo_erro = None
    for llm, modelo, provedor in candidatos:
        try:
            conteudo, tokens = _invocar_llm(llm, msgs)
            return conteudo, tokens, modelo, provedor
        except Exception as e:
            ultimo_erro = e
            if not _is_quota_error(e):
                raise
    raise ultimo_erro


def _invocar_ambos(msgs, history, conversa_id, modo, tipo_prompt):
    resultados = {}

    def chamar(nome, llm):
        conteudo, tokens = _invocar_llm(llm, msgs)
        return nome, conteudo, tokens

    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = {
            ex.submit(chamar, "gemini", _gemini): "gemini",
            ex.submit(chamar, "groq", _groq): "groq",
        }
        for future in as_completed(futures):
            try:
                nome, conteudo, tokens = future.result()
                resultados[nome] = {"conteudo": conteudo, "tokens": tokens}
            except Exception as e:
                resultados[futures[future]] = {"erro": str(e)}

    gemini_res = resultados.get("gemini", {})
    groq_res = resultados.get("groq", {})

    conteudo_principal = gemini_res.get("conteudo", groq_res.get("conteudo", "Erro em ambas as APIs."))
    tokens_principal = gemini_res.get("tokens", 0)

    history.add_ai_message(conteudo_principal)
    inserir_mensagem(conversa_id, "ia", conteudo_principal, modelo=GEMINI_MODEL, tokens=tokens_principal)

    resposta = {
        "resposta": conteudo_principal,
        "modelo": GEMINI_MODEL,
        "provedor": "gemini",
        "modo": modo,
        "tipo_prompt": tipo_prompt,
        "tokens": tokens_principal,
        "comparacao": True,
    }

    if "conteudo" in groq_res:
        resposta["resposta_groq"] = groq_res["conteudo"]
        resposta["modelo_groq"] = GROQ_MODEL
        resposta["tokens_groq"] = groq_res.get("tokens", 0)

    return resposta


if __name__ == "__main__":
    app.run(debug=True)
