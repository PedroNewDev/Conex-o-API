from flask import Flask, request, jsonify, render_template
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1"
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    mensagem = data.get("mensagem", "")

    if not mensagem:
        return jsonify({"erro": "Mensagem vazia"}), 400

    try:
        response = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {"role": "system", "content": "Você é um assistente útil e responde em português."},
                {"role": "user", "content": mensagem}
            ]
        )
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

    return jsonify({
        "resposta": response.choices[0].message.content,
        "modelo": response.model,
        "tokens": response.usage.total_tokens
    })

if __name__ == "__main__":
    app.run(debug=True)
