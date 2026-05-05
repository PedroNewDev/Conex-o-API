from flask import Flask, request, jsonify, render_template, session
from google import genai
from dotenv import load_dotenv
import os
import uuid
from db import inicializar_banco, criar_conversa, buscar_conversa_por_sessao, inserir_mensagem

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "chave-secreta-padrao")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=mensagem
        )
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

    tokens = response.usage_metadata.total_token_count if response.usage_metadata else 0
    inserir_mensagem(conversa_id, "ia", response.text, modelo="gemini-2.0-flash", tokens=tokens)

    return jsonify({
        "resposta": response.text,
        "modelo": "gemini-2.0-flash",
        "tokens": tokens
    })


if __name__ == "__main__":
    app.run(debug=True)
