from flask import Flask, request, jsonify
import google.generativeai as genai
import requests
import os
import logging
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)

CORS(app, resources={r"/summarize_posts": {"origins": "https://news.milho.site"}})

logging.basicConfig(level=logging.INFO)

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY não foi definida no ambiente.")

genai.configure(api_key=api_key)

model = genai.GenerativeModel(model_name="gemini-1.5-flash")

@app.route('/summarize_posts', methods=['GET'])
def summarize_posts():
    url = "https://milharal-news.onrender.com/service/RelevantPotopsts"
    
    try:
        response = requests.get(url)
        response.raise_for_status()

        data = response.json()
        post_texts = []

        for post in data:
            author = post.get('author', {})
            display_name = author.get('displayName', 'Desconhecido')
            handle = author.get('handle', 'Sem handle')
            text = post.get('record', {}).get('text', 'Sem texto')

            post_texts.append(f"{display_name} ({handle}): {text}")

        post_texts_str = " ".join(post_texts)

        prompt = f"Quero que você escreva um resumo em formato de jornal, mas o jornal é diário, então lembre que não é noticia da semana, mas sim do dia de hoje com base nos tópicos mais falados nos posts do Bluesky e da bolha dev, quero que o texto seja divido por tópicos. Transforme o conteúdo em um texto único, contínuo e interessante:\n\n{post_texts_str}"

        summary_response = model.generate_content([prompt])

        if summary_response and summary_response.candidates:
            text = summary_response.candidates[0].content.parts[0].text
            return jsonify({"summary": text})
        else:
            return jsonify({"error": "Nenhum conteúdo gerado."}), 500

    except requests.exceptions.RequestException as req_err:
        logging.error(f"Erro ao fazer a requisição: {req_err}")
        return jsonify({"error": "Erro ao fazer a requisição para obter os posts."}), 500

    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
