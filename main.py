import os
from openai import OpenAI

def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Variável de ambiente OPENAI_API_KEY não encontrada.")

    client = OpenAI(api_key=api_key)

    print("Conectando à API do ChatGPT (OpenAI)...\n")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
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
