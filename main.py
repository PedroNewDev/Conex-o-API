import os
import uuid

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from db import criar_conversa, inicializar_banco, inserir_mensagem

load_dotenv()

MODEL_NAME = "gemini-2.0-flash"


def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Variavel de ambiente GEMINI_API_KEY nao encontrada.")

    inicializar_banco()

    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, google_api_key=api_key)
    pergunta = "Ola! Me diga uma curiosidade interessante sobre inteligencia artificial."
    conversa_id = criar_conversa(str(uuid.uuid4()))

    inserir_mensagem(conversa_id, "usuario", pergunta)

    print("Conectando a API do Gemini (Google) via LangChain...\n")

    response = llm.invoke([HumanMessage(content=pergunta)])
    tokens = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

    inserir_mensagem(conversa_id, "ia", response.content, modelo=MODEL_NAME, tokens=tokens)

    print("=== Resposta da API ===")
    print(f"Modelo: {MODEL_NAME}")
    print(f"\nResposta:\n{response.content}")


if __name__ == "__main__":
    main()
