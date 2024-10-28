from flask import Flask, request, jsonify
import google.generativeai as genai
import requests
import os
import logging
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)

CORS(app, resources={r"/summarize_posts": {"origins": "https://milhonews.vercel.app"}})

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

        prompt = f"Receba os dados dos feeds de hoje do Bluesky, focados nas discussões mais populares entre desenvolvedores, e crie uma matéria jornalística dividida em quatro seções, cada uma abordando um tema relevante do dia. Cada seção deve sintetizar e interligar as postagens, apresentando as interações e opiniões dos usuários de forma fluida, como uma notícia, e cobrindo tópicos como debates sobre desafios de desenvolvimento (ex: 'O Desafio do Dev Marombas'), novidades em ferramentas de programação, insights sobre produtividade, ou tendências emergentes no setor. O tom deve ser jornalístico, informando de maneira coesa e interessante sobre o que foi discutido hoje:\n\n{post_texts_str}"

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

  
@app.route('/get_sub_reddit', methods=['GET'])
def get_sub_reddit():
    subreddit = "programming"
    url = f"https://www.reddit.com/r/{subreddit}/.json"
    headers = {'User-Agent': 'milhonews/1.0 (The Reddit Post Fetcher is a simple and effective application that allows the retrieval of valuable information from the Reddit platform. With a design focused on simplicity and functionality, the application serves as an excellent foundation for future expansions and improvements.)', 'Authorization': 'Bearer REDDIT_API_KEY'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return jsonify({"error": "Falha ao acessar a API do Reddit"}), response.status_code
        
        data = response.json()
        
        posts_data = []
        posts = data.get("data", {}).get("children", [])
        for post in posts:
            post_info = post["data"]
            post_permalink = post_info["permalink"]
            post_url = f"https://www.reddit.com{post_permalink}.json"
            
            posts_data.append({
                "title": post_info["title"],
                "url": post_url
            })
            
            post_response = requests.get(post_url, headers=headers)
            if post_response.status_code == 200:
                post_data = post_response.json()
                
                comments_data = []
                comments = post_data[1].get("data", {}).get("children", [])
                for comment in comments:
                    if comment["kind"] == "t1": 
                        author = comment["data"]["author"]
                        body = comment["data"]["body"]
                        score = comment["data"]["score"]
                        comment_info = {
                            "author": author,
                            "body": body,
                            "score": score
                        }
                        comments_data.append(comment_info)
                        
                        replies = comment["data"].get("replies")
                        if replies and isinstance(replies, dict):  # Verifique se replies é um dicionário
                            reply_data = []
                            for reply in replies["data"]["children"]:
                                if reply["kind"] == "t1":  
                                    reply_author = reply["data"]["author"]
                                    reply_body = reply["data"]["body"]
                                    reply_data.append({
                                        "reply_author": reply_author,
                                        "reply_body": reply_body
                                    })
                            comment_info["replies"] = reply_data
                
                posts_data[-1]["comments"] = comments_data
            else:
                posts_data[-1]["comments"] = [{"error": "Falha ao obter comentários"}]

        return jsonify(posts_data)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(debug=True)
