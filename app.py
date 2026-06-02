import asyncio
import random
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from scrap_prof import scrape_tiktok_videos
from scrap_api import scrap_comentarios
from flask_cors import CORS

app = Flask(__name__)

CORS(app)
load_dotenv()

@app.route("/comments", methods=["GET"])
def index():
    if request.method == "GET":
        video_list = asyncio.run(scrape_tiktok_videos(request.args.get("profile")))

        if not video_list:
                return jsonify({"error": "No se encontraron videos"}), 502
        comments = []
        for v in video_list[:5]:
            comments += asyncio.run(scrap_comentarios(v["id"]))
        
        return jsonify(comments)
    else:
        return render_template("index.html")




if __name__ == "__main__":
    app.run(debug=True)

