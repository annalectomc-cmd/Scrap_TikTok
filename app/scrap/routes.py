import asyncio
from flask import Blueprint, jsonify, request
from app.scraping_tiktok.scrapl import scrape_comments as scrape_tiktok
from app.scraping_yt.scrapl import scrape_comments as scrape_yt

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
    if request.args.get("platform", type=int) == 1:
        comments = asyncio.run(scrape_tiktok(request.args.get("profile"), request.args.get("cant", type=int), request.args.get("type", type=int),  request.args.get("scroll", type=int)))
        if len(comments)> 0:
            return jsonify(comments), 200
        else:
            return jsonify({"message": "no se encontraron comentarios"}), 500
    elif request.args.get("platform", type=int) == 3:
        comments = asyncio.run(scrape_yt(request.args.get("profile"), request.args.get("cant", type=int), request.args.get("type", type=int),  request.args.get("scroll", type=int)))
        if len(comments)> 0:
            return jsonify(comments), 200
        else:
            return jsonify({"message": "no se encontraron comentarios"}), 500
