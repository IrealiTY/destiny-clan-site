import os
import logging
from flask import Flask, current_app
from config import Config, ConfigProd
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    if os.environ['CLANENV'] == 'prod':
        app.config.from_object(ConfigProd)
    else:
        app.config.from_object(Config)

    from app.models import db
    db.init_app(app)

    from app.destiny import api_bp as api
    app.register_blueprint(api)

    if os.environ['CLANENV'] == 'prod':
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

    return app

from app import models