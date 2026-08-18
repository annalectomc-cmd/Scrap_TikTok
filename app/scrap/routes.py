from flask import Blueprint, jsonify, request
from app.scrap.service import ScrapingService


scrap_bp = Blueprint("scrap", __name__)

@scrap_bp.get("/comments")
def get_comments():
    """
    Obtener comentarios
    ---
    parameters:
        - name: platform
          in: query
          type: integer
          required: true
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
        - name: scroll
          in: query
          type: integer
          required: true
    responses:
        200:
            description: Comentarios Obtenidos
        500:
            description: No se obtuvieron comentarios
    """
    platform = request.args.get("platform", type=int)
    profile = request.args.get("profile", type=str)
    cant = request.args.get("cant", type=int)
    content_type = request.args.get("type", type=int)
    scroll = request.args.get("scroll", type=int)

    # Validar parámetros obligatorios
    missing = []

    if platform is None:
        missing.append("platform")

    if not profile:
        missing.append("profile")

    if cant is None:
        missing.append("cant")

    if content_type is None:
        missing.append("type")

    if scroll is None:
        missing.append("scroll")

    if missing:
        return jsonify({
            "message": "Faltan parámetros obligatorios",
            "parameters": missing
        }), 400

    # Validar valores
    if platform not in [1, 2, 3]:
        return jsonify({
            "message": "platform debe ser 1, 2 o 3"
        }), 400

    if cant <= 0:
        return jsonify({
            "message": "cant debe ser mayor que 0"
        }), 400

    if content_type not in [1, 2]:
        return jsonify({
            "message": "type debe ser 1 o 2"
        }), 400

    if scroll <= 0:
        return jsonify({
            "message": "scroll debe ser mayor que 0"
        }), 400
    
    result = ScrapingService.scrape(
        platform=platform,
        profile=profile,
        cant=cant,
        content_type=content_type,
        scroll=scroll
    )

    return jsonify(result), 200
