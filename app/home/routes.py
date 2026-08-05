from flask import Blueprint, jsonify

home_bp = Blueprint("home", __name__)

@home_bp.get("/")
def index():
    """
    Inicio
    ---
    responses:
        200:
            description: Mensaje
    """
    return jsonify({
        "message": "API de Scraping"
    }), 200