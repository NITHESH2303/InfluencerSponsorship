from flask_jwt_extended import jwt_required, get_jwt

from application.models import Sponsor, Campaign
from application.response import create_response, success


def CampaignAPI(Resource):
    @jwt_required()
    def get_campaigns_by_sponsor(self):
        current_user = get_jwt()
        sponsor = Sponsor.query.filter_by(userid=current_user['user_id']).first()

        if not sponsor:
            return create_response("Sponsor not found", 404)

        campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
        campaign_list = [campaign.to_dict() for campaign in campaigns]
        return success(campaign_list)

    @jwt_required()
    def get_all_campaigns(self):
        campaigns = Campaign.query.all()
        all_campaigns = [campaign.to_dict() for campaign in campaigns]
        return success(all_campaigns)