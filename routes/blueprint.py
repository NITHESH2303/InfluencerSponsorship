from crypt import methods

from flask import Blueprint
from flask_restful import Api

from routes.Reports import ReportsAPI
from routes.adRequestAPI import AdRequestAPI
from routes.admin import AdminAPI
from routes.adminOperationsAPI import AdminOperationsAPI
from routes.auth import AuthAPI
from routes.campaigns import CampaignsAPI
from routes.emailAPI import EmailAPI
from routes.enum import EnumAPI
from routes.influencer import InfluencerAPI
from routes.passwordChange import PasswordChangeAPI
from routes.search import SearchAPI
from routes.sponsor import SponsorAPI
from routes.statistics import StatisticsAPI
from routes.user import UserAPI
from services.trigger import TriggerAPI

route_bp = Blueprint('routes', __name__)
api = Api(route_bp)

# AuthAPI routes
api.add_resource(AuthAPI, '/api/auth/login', methods=['POST'], endpoint='auth_login')            # Login
api.add_resource(AuthAPI, '/api/auth/token-refresh', methods=['PATCH'], endpoint='auth_token_refresh')   # Token refresh
api.add_resource(AuthAPI, '/api/auth/logout', methods=['DELETE'], endpoint='auth_logout')         # Logout
api.add_resource(AuthAPI, '/api/auth/change_auth', methods=['PUT'], endpoint='change_auth')

# PasswordChangeAPI
api.add_resource(PasswordChangeAPI, '/api/auth/change_password', methods=['PUT'], endpoint='auth_password_change')

# UserAPI routes with
api.add_resource(UserAPI, '/api/users', methods=['GET'], endpoint='users_list')
api.add_resource(UserAPI, '/api/users/meta', methods=['GET'], endpoint='user_meta')
api.add_resource(UserAPI, '/api/user/signup', methods=['POST'], endpoint='user_signup')           # Sign up
api.add_resource(UserAPI, '/api/user/profile/<int:user_id>', methods=['GET'], endpoint='user_profile')
api.add_resource(UserAPI, '/api/user/profile/edit', methods=['PATCH'], endpoint='edit_user_profile')
api.add_resource(UserAPI, '/api/user/delete', methods=['DELETE'], endpoint='user_delete')         # Soft delete account

# SponsorAPI routes
api.add_resource(SponsorAPI, '/api/sponsor/meta', methods=['GET'], endpoint='sponsor_meta')
api.add_resource(SponsorAPI, '/api/sponsors/list', methods=['GET'], endpoint='sponsor_list')
api.add_resource(SponsorAPI, '/api/register/sponsor', methods=['POST'], endpoint='sponsor_register')
api.add_resource(SponsorAPI, '/api/profile/sponsor/<int:sponsor_id>', methods=['GET'], endpoint='sponsor_profile')

# InfluencerAPI routes
api.add_resource(InfluencerAPI, '/api/register/influencer', methods=['POST'], endpoint='influencer_register')
api.add_resource(InfluencerAPI, '/api/influencer/meta', methods=['GET'], endpoint='influencer_meta')
api.add_resource(InfluencerAPI, '/api/profile/influencer/<int:influencer_id>', methods=['GET'], endpoint='influencer_profile')
api.add_resource(InfluencerAPI, '/api/influencers/list', methods=['GET'], endpoint='influencer_profile_list')
api.add_resource(InfluencerAPI, '/api/influencer/profile/edit', methods=['PATCH'], endpoint='influencer_edit_profile')
api.add_resource(InfluencerAPI, '/api/influencer/campaigns', methods=['GET'], endpoint='influencer_campaign')
api.add_resource(InfluencerAPI, '/api/influencer/adrequests', methods=['GET'], endpoint='influencer_adrequest')
api.add_resource(InfluencerAPI, '/api/influencer/adrequests/negotiate', methods=['PATCH'], endpoint='influencer_negotiate_adrequest')

# AdminAPI routes
api.add_resource(AdminOperationsAPI, '/api/admin/operation/approve_sponsor/<int:sponsor_id>', methods=['POST'], endpoint='admin_approve_sponsor')
api.add_resource(AdminOperationsAPI, '/api/admin/operation/sponsor_approval', methods=['GET'], endpoint='admin_sponsor_approval')
api.add_resource(AdminOperationsAPI, '/api/admin/operation/flag_user', methods=['POST'], endpoint='flag_user')
api.add_resource(AdminOperationsAPI, '/api/admin/operation/unflag_user', methods=['POST'], endpoint='unflag_user')
api.add_resource(AdminOperationsAPI, '/api/admin/operation/flagged_users', methods=['GET'], endpoint='list_flagged_users')
api.add_resource(AdminAPI, '/api/admin/overview', methods=['GET'], endpoint='admin_overview')

#CampaignsAPI routes
api.add_resource(CampaignsAPI, '/api/campaigns', methods=['GET'], endpoint='list_campaigns')
api.add_resource(CampaignsAPI, '/api/sponsor/campaigns/<int:sponsor_id>', methods=['GET'], endpoint='sponsor_campaign')
api.add_resource(CampaignsAPI, '/api/campaigns/<int:campaign_id>', methods=['GET'], endpoint='get_campaign_by_id')
api.add_resource(CampaignsAPI, '/api/campaigns/create_new_campaign', methods=['POST'], endpoint='create_campaigns')
api.add_resource(CampaignsAPI, '/api/campaigns/edit/<int:campaign_id>', methods=['PATCH'], endpoint='edit_campaigns')
api.add_resource(CampaignsAPI, '/api/campaigns/<int:campaign_id>/delete', methods=['DELETE'], endpoint='delete_campaigns')
api.add_resource(CampaignsAPI, '/api/sponsor/campaigns/<int:campaign_id>/status', methods=['PUT'], endpoint='update_campaign_status')

#AdRequest routes
api.add_resource(AdRequestAPI, '/api/adrequests/<int:campaign_id>', methods=['GET'], endpoint='adrequests_by_campaign')
api.add_resource(AdRequestAPI, '/api/campaign/<int:campaign_id>/adrequests/<int:ad_id>', methods=['GET'], endpoint='get_adrequest_id')
api.add_resource(AdRequestAPI, '/api/influencer/ad-requests/<int:influencer_id>', methods=['GET'], endpoint='get_adrequest_influencer')
api.add_resource(AdRequestAPI, '/api/adrequests/<int:influencer_id>/new', methods=['POST'], endpoint='create_adrequests')
api.add_resource(AdRequestAPI, '/api/adrequests/<int:ad_id>/edit', methods=['PUT'], endpoint='edit_adrequests')
api.add_resource(AdRequestAPI, '/api/influencer/ad-requests/<int:ad_id>/status', methods=['PATCH'], endpoint='update_adrequest_status')
api.add_resource(AdRequestAPI, '/api/influencer/negotiate/<int:ad_id>', methods=['PATCH'], endpoint='negotiate_adrequest')
api.add_resource(AdRequestAPI, '/api/adrequests/<int:ad_id>/accept_negotiation', methods=['PATCH'], endpoint='accept_adrequest_negotiation')
api.add_resource(AdRequestAPI, '/api/adrequests/<int:ad_id>/delete', methods=['DELETE'], endpoint='delete_adrequests')

# Enum routes
api.add_resource(EnumAPI, '/api/niches', methods=['GET'], endpoint='list_niches')
api.add_resource(EnumAPI, '/api/adstatus', methods=['GET'], endpoint='list_adstatus')

#emailAPI routes
api.add_resource(EmailAPI, '/api/send_emails', methods=['POST'], endpoint='list_emails')
api.add_resource(EmailAPI, '/api/notify/flag_users', methods=['POST'], endpoint='notify_flag_users')

# triggerJobs routes
api.add_resource(TriggerAPI, '/api/trigger/daily_remainders', methods=['POST'], endpoint='trigger_daily_remainders')

#export routes
api.add_resource(ReportsAPI, '/api/export_campaigns/<int:sponsor_id>', methods=['POST'], endpoint='export_campaigns')
api.add_resource(ReportsAPI, '/api/sponsor/stats/<int:sponsor_id>', methods=['GET'], endpoint='sponsor_stats')

# search routes
api.add_resource(SearchAPI, '/api/search', methods=['GET'], endpoint='search')

#statisrics routes
api.add_resource(StatisticsAPI, '/api/statistics', methods=['GET'], endpoint='statistics')

def init_app(app):
    app.register_blueprint(route_bp)
