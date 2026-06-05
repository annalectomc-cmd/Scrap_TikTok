import asyncio
import random
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from scr_driverless import scrape_profile
from scrap_prof import scrape_tiktok_videos
from scrap_api import scrap_comentarios
from flask_cors import CORS

app = Flask(__name__)

CORS(app)
load_dotenv()

@app.route("/comments", methods=["GET"])
def index():
    if request.method == "GET":
        #video_list, token = asyncio.run(scrape_tiktok_videos(request.args.get("profile")))
        comments = asyncio.run(scrape_profile(request.args.get("profile")))
        # if not video_list:
        #         return jsonify({"error": "No se encontraron videos"}), 444
        # comments = []
        # for v in video_list[:5]:
        #     comments += asyncio.run(scrap_comentarios(v["id"]))
        
        return jsonify(comments), 200
    else:
        return render_template("index.html")




if __name__ == "__main__":
    app.run(debug=True)

