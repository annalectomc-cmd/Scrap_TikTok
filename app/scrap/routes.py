from flask import Blueprint, jsonify, request
from app.scrap.jobs import scraping_jobs
from app.scrap.service import ScrapingService


scrap_bp = Blueprint("scrap", __name__)


def _scraping_parameters(source):
    """Valida una solicitud JSON (o query string) y devuelve sus parámetros."""
    def number(name):
        try:
            return int(source.get(name))
        except (TypeError, ValueError):
            return None

    platform = number("platform")
    profile = source.get("profile", "").strip() if isinstance(source.get("profile"), str) else ""
    cant = number("cant")
    content_type = number("type")
    scroll = number("scroll")

    missing = [
        name for name, value in {
            "platform": platform,
            "profile": profile,
            "cant": cant,
            "type": content_type,
            "scroll": scroll,
        }.items() if value is None or value == ""
    ]
    if missing:
        return None, {"message": "Faltan o son inválidos parámetros obligatorios", "parameters": missing}

    if platform not in [1, 2, 3]:
        return None, {"message": "platform debe ser 1, 2 o 3"}
    if cant <= 0:
        return None, {"message": "cant debe ser mayor que 0"}
    if content_type not in [1, 2]:
        return None, {"message": "type debe ser 1 o 2"}
    if scroll <= 0:
        return None, {"message": "scroll debe ser mayor que 0"}

    return {
        "platform": platform,
        "profile": profile,
        "cant": cant,
        "content_type": content_type,
        "scroll": scroll,
    }, None


@scrap_bp.post("/jobs")
def create_job():
    """Inicia un scraping en segundo plano.

    El estado `captcha_required` incluye `browser_url`. El frontend debe abrir
    esa URL en un iframe o en una pestaña para que el usuario resuelva el
    CAPTCHA; el trabajo continúa automáticamente cuando éste desaparece.
    """
    source = request.get_json(silent=True)
    if not isinstance(source, dict):
        source = request.args

    parameters, error = _scraping_parameters(source)
    if error:
        return jsonify(error), 400

    return jsonify(scraping_jobs.create(parameters)), 202


@scrap_bp.get("/jobs/<job_id>")
def get_job(job_id):
    job = scraping_jobs.get(job_id)
    if job is None:
        return jsonify({"message": "Trabajo no encontrado"}), 404
    return jsonify(job), 200

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
    
    comments, videos = ScrapingService.scrape(
        platform=platform,
        profile=profile,
        cant=cant,
        content_type=content_type,
        scroll=scroll
    )

    if len(comments) == 0:
        return jsonify({"message": "no se encontraron comentarios"}), 500
    else:
        return jsonify({"comments": comments,
                        "videos": videos}), 200
