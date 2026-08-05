from functools import wraps
from flask import request
from firebase_admin import auth

def firebase_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        token = request.headers["Authorization"].split(" ")[1]

        auth.verify_id_token(token)

        return func(*args, **kwargs)

    return wrapper