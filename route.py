from flask_restful import Api
from flask import Blueprint

from routes.auth import AuthAPI

bp = Blueprint('routes', __name__)
api = Api(bp)

api.add_resource(AuthAPI, '/api/auth/login')


def init_app(app):
    app.register_blueprint(bp)
