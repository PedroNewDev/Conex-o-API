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


def escolher_provedor(mensagem: str, modo: str) -> str:
    """Retorna 'gemini', 'groq' ou 'ambos'."""
    if modo in ("tecnico", "suporte_tecnico"):
        return "gemini"
    if modo == "detalhado":
        return "ambos"
    if modo == "professor":
        return "groq"

    msg_lower = mensagem.lower()
    palavras = set(re.findall(r"\w+", msg_lower))
    if palavras & _TECNICO_KWS:
        return "gemini"
    return "groq"
