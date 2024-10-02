from flask_restful import Api
from flask import Blueprint

from routes.auth import AuthAPI

route_bp = Blueprint('routes', __name__)
api = Api(route_bp)

api.add_resource(AuthAPI, '/api/auth/login')


def init_app(app):
    app.register_blueprint(route_bp)