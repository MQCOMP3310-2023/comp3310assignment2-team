import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# init SQLAlchemy so we can use it later in our models
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    with open("secret_key", "r") as secret_file:
        app.secret_key = secret_file.readline()

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurantmenu.db'

    db.init_app(app)

    # blueprint for auth routes in our app
    from .json import json as json_blueprint
    app.register_blueprint(json_blueprint)

    # blueprint for non-auth parts of app
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
