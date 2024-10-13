from flask_restful import Api
from flask import Blueprint

from routes.auth import AuthAPI
from routes.user import UserAPI

route_bp = Blueprint('routes', __name__)
api = Api(route_bp)

# AuthAPI routes with unique endpoints
api.add_resource(AuthAPI, '/api/auth/login', methods=['POST'], endpoint='auth_login')            # Login
api.add_resource(AuthAPI, '/api/auth/token-refresh', methods=['PATCH'], endpoint='auth_token_refresh')   # Token refresh
api.add_resource(AuthAPI, '/api/auth/logout', methods=['DELETE'], endpoint='auth_logout')         # Logout

# UserAPI routes with unique endpoints
api.add_resource(UserAPI, '/api/user/signup', methods=['POST'], endpoint='user_signup')           # Sign up
api.add_resource(UserAPI, '/api/user/profile', methods=['GET', 'PUT'], endpoint='user_profile')    # Profile management (GET for fetching profile, PUT for updating profile)
api.add_resource(UserAPI, '/api/user/delete', methods=['DELETE'], endpoint='user_delete')         # Soft delete account

def init_app(app):
    app.register_blueprint(route_bp)
