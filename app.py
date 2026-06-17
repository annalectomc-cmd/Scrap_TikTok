import asyncio
import random
from flask import Flask, jsonify, render_template, request
from scr_driverless import scrape_profile
from scrapl import scrape_comments
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/comments", methods=["GET"])
def index():
    if request.method == "GET":
        comments = asyncio.run(scrape_comments("https://www.tiktok.com/@"+request.args.get("profile")))
        return jsonify(comments), 200
    




if __name__ == "__main__":
    app.run(debug=True)

