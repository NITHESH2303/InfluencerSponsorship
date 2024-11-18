from flask import Blueprint
from flask_restful import Api

from routes.admin import AdminAPI
from routes.adminOperationsAPI import AdminOperationsAPI
from routes.auth import AuthAPI
from routes.campaigns import CampaignsAPI
from routes.influencer import InfluencerAPI
from routes.sponsor import SponsorAPI
from routes.user import UserAPI

route_bp = Blueprint('routes', __name__)
api = Api(route_bp)

# AuthAPI routes with unique endpoints
api.add_resource(AuthAPI, '/api/auth/login', methods=['POST'], endpoint='auth_login')            # Login
api.add_resource(AuthAPI, '/api/auth/token-refresh', methods=['PATCH'], endpoint='auth_token_refresh')   # Token refresh
api.add_resource(AuthAPI, '/api/auth/logout', methods=['DELETE'], endpoint='auth_logout')         # Logout

# UserAPI routes with unique endpoints
api.add_resource(UserAPI, '/api/user/signup', methods=['POST'], endpoint='user_signup')           # Sign up
api.add_resource(UserAPI, '/api/user/profile/<string:username>', methods=['GET', 'PUT'], endpoint='user_profile')    # Profile management (GET for fetching profile, PUT for updating profile)
api.add_resource(UserAPI, '/api/user/delete', methods=['DELETE'], endpoint='user_delete')         # Soft delete account

# SponsorAPI routes
api.add_resource(SponsorAPI, '/api/sponsor/meta', methods=['GET'], endpoint='sponsor_meta')
api.add_resource(SponsorAPI, '/api/register/sponsor', methods=['POST'], endpoint='sponsor_register')
# InfluencerAPI routes
api.add_resource(InfluencerAPI, '/api/register/influencer', methods=['POST'], endpoint='influencer_register')

# AdminAPI routes
api.add_resource(AdminOperationsAPI, '/api/admin/operation/approve_sponsor/<int:sponsor_id>', methods=['POST'], endpoint='admin_approve_sponsor')
api.add_resource(AdminOperationsAPI, '/api/admin/operation/sponsor_approval', methods=['GET'], endpoint='admin_sponsor_approval')
api.add_resource(AdminAPI, '/api/admin/overview', methods=['GET'], endpoint='admin_overview')

#CampaignsAPI routes
api.add_resource(CampaignsAPI, '/api/campaigns', methods=['GET'], endpoint='list_campaigns')
api.add_resource(CampaignsAPI, '/api/campaigns/<int:sponsor_id>', methods=['GET'], endpoint='sponsor_campaign')
api.add_resource(CampaignsAPI, '/api/campaigns/create_new_campaign', methods=['POST'], endpoint='create_campaigns')
api.add_resource(CampaignsAPI, '/api/campaigns/edit/<int:campaign_id>', methods=['PUT'], endpoint='edit_campaigns')
api.add_resource(CampaignsAPI, '/api/campaigns/<int:campaign_id>/delete', methods=['DELETE'], endpoint='delete_campaigns')

def init_app(app):
    app.register_blueprint(route_bp)
