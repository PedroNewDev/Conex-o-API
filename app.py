import os
import uuid

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_google_genai import ChatGoogleGenerativeAI

from db import buscar_conversa_por_sessao, criar_conversa, inicializar_banco, inserir_mensagem

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave-secreta-padrao")

MODEL_NAME = "gemini-2.0-flash"
llm = ChatGoogleGenerativeAI(model=MODEL_NAME, google_api_key=os.getenv("GEMINI_API_KEY"))
conversation_histories: dict[int, InMemoryChatMessageHistory] = {}

with app.app_context():
    inicializar_banco()


@app.route("/")
def index():
    if "sessao_id" not in session:
        session["sessao_id"] = str(uuid.uuid4())
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensagem = data.get("mensagem", "")

    if not mensagem:
        return jsonify({"erro": "Mensagem vazia"}), 400

    sessao_id = session.get("sessao_id", str(uuid.uuid4()))
    conversa_id = buscar_conversa_por_sessao(sessao_id)
    if not conversa_id:
        conversa_id = criar_conversa(sessao_id)

    inserir_mensagem(conversa_id, "usuario", mensagem)

    history = conversation_histories.setdefault(conversa_id, InMemoryChatMessageHistory())
    history.add_user_message(mensagem)

    try:
        response = llm.invoke(history.messages)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

    history.add_ai_message(response.content)
    tokens = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0
    inserir_mensagem(conversa_id, "ia", response.content, modelo=MODEL_NAME, tokens=tokens)

    return jsonify({
        "resposta": response.content,
        "modelo": MODEL_NAME,
        "tokens": tokens
    })


if __name__ == "__main__":
    app.run(debug=True)
