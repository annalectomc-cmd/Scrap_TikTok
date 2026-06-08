import asyncio
import random
from flask import Flask, jsonify, render_template, request
from scr_driverless import scrape_profile
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/comments", methods=["GET"])
def index():
    if request.method == "GET":
        comments = asyncio.run(scrape_profile(request.args.get("profile")))
        return jsonify(comments), 200
    else:
        return render_template("index.html")




if __name__ == "__main__":
    app.run(debug=True)

