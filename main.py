import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def main():
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        raise ValueError("Variável de ambiente XAI_API_KEY não encontrada.")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.x.ai/v1"
    )

    print("Conectando à API do Grok (xAI)...\n")

    response = client.chat.completions.create(
        model="grok-beta",
        messages=[
            {"role": "system", "content": "Você é um assistente útil."},
            {"role": "user", "content": "Olá! Me diga uma curiosidade interessante sobre inteligência artificial."}
        ]
    )

    resposta = response.choices[0].message.content
    modelo_usado = response.model
    tokens_usados = response.usage.total_tokens

    print("=== Resposta da API ===")
    print(f"Modelo: {modelo_usado}")
    print(f"Tokens utilizados: {tokens_usados}")
    print(f"\nResposta:\n{resposta}")

if __name__ == "__main__":
    main()
