from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

#from app.extensions.db import db
from app.extensions.firebase import init_firebase

from app.home.routes import home_bp
from app.auth.routes import auth_bp
from app.scrap.routes import scrap_bp
#from app.users.routes import users_bp


def create_app():

    app = Flask(__name__)

    #app.config.from_object("config.Config")

    CORS(app)
    Swagger(app)

    #db.init_app(app)

    #firestore_db = init_firebase()

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(scrap_bp, url_prefix="/scrap")
    

    return app