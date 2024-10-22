from flask import Flask, request, jsonify
import google.generativeai as genai
import requests
import os
import logging

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

os.environ["GOOGLE_API_KEY"] = "GOOGLE_API_KEY"
api_key = os.environ["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)

model = genai.GenerativeModel(model_name="gemini-1.5-flash")

@app.route('/ask', methods=['GET'])
def ask_question():
    question = request.args.get('question')

    if not question:
        return jsonify({"error": "O parâmetro 'question' é obrigatório."}), 400

    try:
        # Gere o conteúdo com a pergunta
        response = model.generate_content([question])
        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/summarize_posts', methods=['GET'])
def summarize_posts():
    url = "http://localhost:8083/service/RelevantPotopsts"
    
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
        prompt = f"Quero que você escreva um resumo em formato de jornal com base nos tópicos mais falados nos posts do Bluesky e da bolha dev. Transforme o conteúdo em um texto único, contínuo e interessante:\n\n{post_texts_str}"

        summary_response = model.generate_content(prompt)

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
