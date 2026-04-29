import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def main():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Variável de ambiente GEMINI_API_KEY não encontrada.")

    client = genai.Client(api_key=api_key)

    print("Conectando à API do Gemini (Google)...\n")

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Olá! Me diga uma curiosidade interessante sobre inteligência artificial."
    )

    print("=== Resposta da API ===")
    print(f"Modelo: gemini-2.0-flash")
    print(f"\nResposta:\n{response.text}")

if __name__ == "__main__":
    main()
