import re

MODOS = {
    "tecnico": (
        "Você é um assistente técnico especializado. Responda com precisão técnica, "
        "use terminologia correta da área, inclua detalhes de implementação quando relevante. "
        "Prefira respostas estruturadas com exemplos de código quando aplicável. "
        "Não simplifique conceitos técnicos importantes."
    ),
    "resumido": (
        "Você é um assistente conciso e direto. "
        "Responda em no máximo 3 parágrafos curtos. "
        "Vá direto ao ponto principal sem introduções desnecessárias. "
        "Evite repetições e rodeios."
    ),
    "professor": (
        "Você é um professor didático e paciente. Explique conceitos de forma clara e acessível. "
        "Use analogias do cotidiano, dê exemplos práticos e organize o conteúdo em passos quando possível. "
        "Adapte a linguagem para facilitar o aprendizado do iniciante. "
        "Encoraje perguntas de acompanhamento."
    ),
    "detalhado": (
        "Você é um analista aprofundado. Forneça análises completas e abrangentes. "
        "Explore múltiplos ângulos, considere casos de uso, vantagens, desvantagens e alternativas. "
        "Não omita pontos importantes. Organize a resposta com seções claras quando necessário."
    ),
    "suporte_tecnico": (
        "Você é um especialista em suporte técnico. Foque em diagnosticar problemas. "
        "Identifique possíveis causas raiz, forneça soluções passo a passo com checklist quando aplicável. "
        "Sugira prevenções para evitar recorrência. Seja objetivo e orientado à solução."
    ),
}

MODO_PADRAO = "resumido"

_TECNICO_KWS = {
    "código", "code", "programar", "programming", "bug", "erro", "error", "api",
    "banco", "database", "sql", "python", "javascript", "typescript", "html", "css",
    "função", "function", "algoritmo", "algorithm", "deploy", "servidor", "server",
    "framework", "library", "biblioteca", "debug", "compile", "docker", "git",
    "json", "http", "rest", "graphql", "query", "classe", "class", "objeto", "object",
    "variável", "variable", "loop", "array", "lista", "dict", "exception", "import",
    "módulo", "module", "package", "pip", "npm", "endpoint", "request", "response",
}


def aplicar_tipo_prompt(mensagem: str, tipo: str) -> str:
    if tipo == "estruturado":
        return (
            f"Contexto: O usuário precisa de ajuda com a seguinte questão.\n"
            f"Pergunta: {mensagem}\n"
            f"Formato esperado: Resposta clara, bem organizada e focada no tópico.\n"
            f"Restrições: Mantenha o foco na questão solicitada, sem desvios."
        )
    if tipo == "especializado":
        return (
            f"[CONSULTA ESPECIALIZADA]\n"
            f"Nível de profundidade requerido: Alto\n"
            f"Questão: {mensagem}\n"
            f"Requisitos: Inclua referências técnicas relevantes, melhores práticas, "
            f"considerações avançadas e possíveis armadilhas ou limitações conhecidas."
        )
    return mensagem


# ──────────────────────────────────────────────────────────────────────────
# ROTEAMENTO INTELIGENTE
# Cada IA é escolhida conforme a força dela para o tipo de prompt:
#   gemini   → raciocínio técnico, código, debugging
#   groq     → texto didático/conversacional, baixa latência
#   cerebras → respostas longas/analíticas (inferência muito rápida)
#   gpt      → criativo / redação / casos gerais
# ──────────────────────────────────────────────────────────────────────────

# Forças declaradas de cada provedor (usadas pelo roteador e pela IA-juíza)
FORCAS_PROVEDOR = {
    "gemini":   "raciocínio técnico, código e debugging",
    "groq":     "explicações didáticas e respostas rápidas",
    "cerebras": "análises longas e aprofundadas",
    "gpt":      "escrita criativa e redação",
}

_CRIATIVO_KWS = {
    "escreva", "crie", "criar", "história", "historia", "conto", "poema",
    "redação", "redacao", "story", "write", "poem", "essay", "roteiro",
    "slogan", "post", "legenda", "e-mail", "email", "carta",
}

_ANALISE_KWS = {
    "compare", "comparar", "analise", "análise", "analisar", "vantagens",
    "desvantagens", "prós", "contras", "explique", "detalhe", "diferença",
    "diferenças", "por que", "porque", "impacto", "consequências",
}


def _classificar_heuristica(mensagem: str, modo: str):
    """Nível 1 — decisão imediata por modo/palavras-chave.
    Retorna (provedor, motivo) ou (None, None) se for ambíguo (vai pra IA-juíza).
    """
    # Modos com destino fixo
    if modo in ("tecnico", "suporte_tecnico"):
        return "gemini", "Modo técnico → Gemini (forte em raciocínio técnico)"
    if modo == "detalhado":
        return "ambos", "Modo detalhado → compara Gemini e Groq lado a lado"
    if modo == "professor":
        return "groq", "Modo professor → Groq (didático e rápido)"

    palavras = set(re.findall(r"\w+", mensagem.lower()))

    # Sinais fortes primeiro (criativo e analítico são intenções claras);
    # técnico genérico fica por último para não "engolir" os demais.
    if palavras & _CRIATIVO_KWS:
        return "gpt", "Pedido criativo/redação → GPT (escrita)"
    if palavras & _ANALISE_KWS:
        return "cerebras", "Pedido analítico → Cerebras (análise longa e rápida)"
    if palavras & _TECNICO_KWS:
        return "gemini", "Detectei termos técnicos → Gemini (código/debug)"

    # Ambíguo: deixa a IA-juíza decidir
    return None, None


def _classificar_com_juiz(mensagem: str, llm_juiz, provedores_ativos):
    """Nível 2 — uma IA rápida classifica a intenção e escolhe o provedor.
    `llm_juiz` é qualquer LLM já instanciado (idealmente Groq, pela latência).
    Retorna (provedor, motivo). Cai em fallback seguro se algo falhar.
    """
    opcoes = ", ".join(p for p in ("gemini", "groq", "cerebras", "gpt") if p in provedores_ativos)
    prompt_juiz = (
        "Você é um roteador de IAs. Classifique a pergunta do usuário e responda "
        "APENAS com uma destas palavras, sem pontuação ou explicação: "
        f"{opcoes}.\n\n"
        "Critério:\n"
        "- gemini: código, técnico, lógica\n"
        "- groq: dúvida simples, conversa, didático\n"
        "- cerebras: análise longa, comparação aprofundada\n"
        "- gpt: criativo, redação, texto livre\n\n"
        f"Pergunta: {mensagem}\n"
        "Resposta (uma palavra):"
    )
    try:
        resp = llm_juiz.invoke(prompt_juiz)
        escolha = (resp.content or "").strip().lower()
        escolha = re.sub(r"[^a-z]", "", escolha)
        if escolha in provedores_ativos:
            return escolha, f"IA-juíza classificou e escolheu {escolha.upper()} ({FORCAS_PROVEDOR.get(escolha, '')})"
    except Exception:
        pass
    # Fallback seguro
    destino = "gemini" if "gemini" in provedores_ativos else next(iter(provedores_ativos))
    return destino, f"IA-juíza indisponível → fallback para {destino.upper()}"


def rotear(mensagem: str, modo: str, llm_juiz=None, provedores_ativos=None):
    """Roteador combinado (Nível 1 + Nível 2).

    Retorna dict:
        {provedor, motivo, etapas: [...] }
    etapas é uma trilha legível para exibir o raciocínio na interface.
    """
    if provedores_ativos is None:
        provedores_ativos = {"gemini"}

    etapas = []

    # Nível 1 — heurística
    provedor, motivo = _classificar_heuristica(mensagem, modo)
    if provedor is not None:
        # Se o destino heurístico não estiver ativo, rebaixa para gemini
        if provedor not in ("ambos",) and provedor not in provedores_ativos:
            etapas.append(f"{provedor.upper()} indisponível → usando Gemini")
            provedor = "gemini"
            motivo = "Provedor preferido inativo → Gemini"
        etapas.append("Heurística: " + motivo)
        return {"provedor": provedor, "motivo": motivo, "etapas": etapas}

    # Nível 2 — IA-juíza (caso ambíguo)
    etapas.append("Heurística: caso ambíguo, consultando IA-juíza…")
    if llm_juiz is not None:
        provedor, motivo = _classificar_com_juiz(mensagem, llm_juiz, provedores_ativos)
    else:
        provedor = "gemini" if "gemini" in provedores_ativos else next(iter(provedores_ativos))
        motivo = "Sem IA-juíza disponível → Gemini (padrão)"
    etapas.append(motivo)
    return {"provedor": provedor, "motivo": motivo, "etapas": etapas}


def escolher_provedor(mensagem: str, modo: str) -> str:
    """Compatibilidade: retorna apenas a string do provedor (Nível 1 puro).
    Mantida para qualquer código que ainda chame a versão antiga.
    """
    provedor, _ = _classificar_heuristica(mensagem, modo)
    return provedor if provedor is not None else "groq"
