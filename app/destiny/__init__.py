import app.destiny.client
from flask import Blueprint
from flask_restplus import Api

api_bp = Blueprint('api_bp', __name__, url_prefix="/api")
api_rest = Api(api_bp, ui=False, doc=False)

from .resources import *