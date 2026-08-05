from flask import Blueprint, request, jsonify
from app.auth.service import AuthService

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login")
def login():
    """
    Autenticación
    ---
    parameters:
        - name: token
          in: query
          type: string
          required: true
    responses:
        200:
            description: Usuario Autenticado
    """
    token = request.json.get("token")

    user = AuthService.verify_token(token)

    return jsonify(user), 200