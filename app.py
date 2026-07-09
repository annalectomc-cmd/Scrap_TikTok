import asyncio, os, threading, webbrowser, sys
from flask import Flask, jsonify, request, send_from_directory
from scr_driverless import scrape_profile
from scrapl import scrape_comments
from flask_cors import CORS
from flasgger import Swagger

def resource_path(relative):
    base = getattr(sys, "MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative)

app = Flask(__name__
            #despliegue
            # ,static_folder=resource_path("dist"),
            # static_url_path=""
            )
CORS(app)
Swagger(app)

@app.route("/", methods=["GET"])
def index():
    """
    Inicio
    ---
    responses:
        200:
            description: Mensaje
    """
    #desarrollo
    if request.method =="GET":
        return "Bienvenido", 200
    #despliegue
    # return send_from_directory(app.static_folder, "index.html")
    
@app.route("/comments", methods=["GET"])
def get_comments():
    """
    Obtener comentarios
    ---
    parameters:
        - name: profile
          in: query
          type: string
          required: true
        - name: cant
          in: query
          type: integer
          required: true
        - name: type
          in: query
          type: integer
          required: true
    responses:
        200:
            description: Comentarios Obtenidos
        500:
            description: No se obtuvieron comentarios
    """
    if request.method == "GET":
        comments = asyncio.run(scrape_comments(request.args.get("profile"), request.args.get("cant", type=int), request.args.get("type", type=int)))
        if len(comments)> 0:
            return jsonify(comments), 200
        else:
            return jsonify({"message": "no se encontraron comentarios"}), 500
#despliegue
# @app.route("/<path:path>")
# def serve_react(path):
#     full = os.path.join(app.static_folder, path)
#     if os.path.exists(full):
#         comments = send_from_directory(app.static_folder, path)
#         return jsonify(comments), 200

def browser_ver():
    ruta = os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "ms-playwright")
    return os.path.exists(ruta) and os.listdir(ruta)

def install_browser():

    if browser_ver():
        return
    
    try:
        from scrapling.cli import install
        install([], standalone_mode=False)

    except Exception as e:
        print("error")

def open_browser():
    webbrowser.open("http://localhost:5000")


if __name__ == "__main__":
    #desarrollo
    app.run(debug=True)
    #despliegue
    # install_browser()
    # threading.Timer(1.5, open_browser).start()
    # app.run(port=5000)
