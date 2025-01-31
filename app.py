from flask import Flask, request, jsonify
import google.generativeai as genai
import requests
import os
import logging
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)

CORS(app, resources={
    r"/summarize_posts": {"origins": ["https://www.milho.site"]},
    r"/is_opportunity": {"origins": ["https://milharal-news.onrender.com"]},
    r"/keywords": {"origins": ["https://milharal-news.onrender.com"]},
    r"/question": {"origins": ["https://milharal-news.onrender.com"]}
})

logging.basicConfig(level=logging.INFO)

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("GOOGLE_API_KEY não foi definida no ambiente.")

genai.configure(api_key=api_key)

model = genai.GenerativeModel(model_name="gemini-1.5-flash")

@app.route('/keywords', methods=['GET'])
def generate_keywords():
    try:
        user_input = request.args.get("text")

        if not user_input:
            return jsonify({"error": "Texto não fornecido."}), 400

        prompt = (
    f"Quais são as principais palavras-chave e tópicos específicos que capturam o contexto do texto a seguir? Responda com uma lista de 190 palavras ou termos diretamente relacionados ao universo abordado, evitando termos genéricos como 'programação' ou 'tecnologia'. Em vez disso, foque em palavras e tópicos específicos que reflitam o conteúdo de forma precisa. Por exemplo, para um texto sobre Java, liste palavras como JPA, Spring Boot, Tomcat, arquitetura REST, entre outras que representem bem o assunto.\n\n\"{user_input}\""
            )        
        keywords_response = model.generate_content([prompt])

        if keywords_response and keywords_response.candidates:
            response_text = keywords_response.candidates[0].content.parts[0].text.strip()
            keywords = [keyword.strip() for keyword in response_text.split(',') if keyword.strip()]
            return jsonify({"keywords": keywords})
        else:
            return jsonify({"error": "Nenhum conteúdo gerado."}), 500

    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/question', methods=['GET'])
def question():
    try:
    
        post_text = request.args.get("text")

        if not post_text:
            return jsonify({"error": "Texto do post não fornecido."}), 400

        prompt = f"Este texto faz sentido em relação ao objetivo pedido pelo usuário? Avalie se o conteúdo claramente corresponde ao tema especificado pelo usuário e atende ao propósito pretendido. Responda apenas com '{{\"is_relevant\": true}}' se o conteúdo do post estiver alinhado ao objetivo do usuário, ou '{{\"is_not_relevant\": false}}' se o conteúdo não estiver alinhado:\n\n\"{post_text}\""
        verification_response = model.generate_content([prompt])

        if verification_response and verification_response.candidates:
            response_text = verification_response.candidates[0].content.parts[0].text.strip().lower()

            if "true" in response_text:
                return jsonify({"question": True})
            elif "false" in response_text:
                return jsonify({"question": False})
            else:
                return jsonify({"error": "Resposta inesperada do modelo."}), 500
        else:
            return jsonify({"error": "Nenhum conteúdo gerado."}), 500

    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/is_opportunity', methods=['GET'])
def is_opportunity():
    try:
    
        post_text = request.args.get("text")

        if not post_text:
            return jsonify({"error": "Texto do post não fornecido."}), 400

        prompt = f"Este texto refere-se a um anúncio de vaga de emprego? Ele deve claramente se referir a uma oportunidade de trabalho em uma empresa, e não pode ser sobre cursos ou treinamentos. Responda apenas com '{{\"is_opportunity\": true}}' se for um anúncio de emprego, ou '{{\"is_not_opportunity\": false}}' se não for:\n\n\"{post_text}\""
        verification_response = model.generate_content([prompt])

        if verification_response and verification_response.candidates:
            response_text = verification_response.candidates[0].content.parts[0].text.strip().lower()

            if "true" in response_text:
                return jsonify({"is_opportunity": True})
            elif "false" in response_text:
                return jsonify({"is_opportunity": False})
            else:
                return jsonify({"error": "Resposta inesperada do modelo."}), 500
        else:
            return jsonify({"error": "Nenhum conteúdo gerado."}), 500

    except Exception as e:
        logging.error(f"Erro inesperado: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/summarize_posts', methods=['GET'])
def summarize_posts():
    url = "https://milharal-news.onrender.com/post"
    
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

        prompt = f"Receba os dados dos feeds de hoje do Bluesky, focados exclusivamente em tretas entre influencers. Crie uma matéria com 10 seções, cada uma cobrindo uma treta relevante do dia. O tom deve ser direto e analítico, destacando: O que iniciou a briga, os argumentos de cada lado, indiretas, exposed e repercussão, consequências para os envolvidos. O objetivo é relatar os conflitos entre devs influentes sem floreios, apenas apresentando os fatos e impactos na comunidade:\n\n{post_texts_str}"

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
