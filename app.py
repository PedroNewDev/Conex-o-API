from flask import Flask, request, jsonify, render_template
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=mensagem
        )
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

    return jsonify({
        "resposta": response.text,
        "modelo": "gemini-2.0-flash",
        "tokens": response.usage_metadata.total_token_count if response.usage_metadata else 0
    })

if __name__ == "__main__":
    app.run(debug=True)
