from datetime import datetime

from flask import request
from flask_jwt_extended import jwt_required, get_jwt
from flask_restful import Resource, reqparse, abort

from application import db
from application.models import Sponsor, Campaign, CampaignNiche, CampaignStatus
from application.response import create_response, success, internal_server_error, resource_not_found
from routes.decorators import jwt_roles_required
from routes.sponsor import SponsorAPI


class CampaignsAPI(Resource):

    def __init__(self):
        self.campaign_input_fields = reqparse.RequestParser()
        self.campaign_input_fields.add_argument("campaign_name", type=str, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("description", type=str, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("start_date", type=str, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("end_date", type=str, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("budget", type=int, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("visibility", type=bool, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("niche", type=str, required=True, help="This field cannot be blank")

    @staticmethod
    def __get_campaigns_by_sponsor(sponsor_id=None):
        current_user = get_jwt()
        user_id = current_user["user_id"]
        if sponsor_id is None:
            sponsor = Sponsor.query.filter_by(userid=user_id).one_or_none()
        else:
            sponsor = Sponsor.query.filter_by(id=sponsor_id).one_or_none()

        if not sponsor:
            return create_response("Sponsor not found", 404)

        niche = request.args.get("niche")
        min_budget = request.args.get("min_budget", type=int)
        max_budget = request.args.get("max_budget", type=int)

        query = Campaign.query.filter_by(sponsor_id=sponsor.id, deleted_on=None)

        is_owner_request = (sponsor.userid == user_id)

        if not is_owner_request:
            query = query.filter(Campaign.visibility != 1)

        if niche:
            query = query.filter(Campaign.niche.ilike(f"%{niche}%"))
        if min_budget is not None:
            query = query.filter(Campaign.budget >= min_budget)
        if max_budget is not None:
            query = query.filter(Campaign.budget <= max_budget)

        campaigns = query.all()
        campaign_list = [campaign.to_dict() for campaign in campaigns]
        return success(campaign_list)

    @staticmethod
    def __get_all_campaigns():
        campaigns = Campaign.query.all()
        all_campaigns = [campaign.to_dict() for campaign in campaigns if campaign.deleted_on is None]
        return success(all_campaigns)

    @staticmethod
    def __get_campaign_by_id(campaign_id):
        campaign = Campaign.query.filter_by(id=campaign_id).one()
        if not campaign:
            return resource_not_found("Campaign not found")
        return success(campaign.to_dict())

    def __create_campaign(self):
        args = self.campaign_input_fields.parse_args()
        name = args['campaign_name']
        description = args['description']
        start_date = args['start_date']
        end_date = args['end_date']
        budget = args['budget']
        visibility = args['visibility']
        niche = args['niche']
        try:
            current_user = get_jwt()
            sponsor_id = SponsorAPI.get_sponsor_from_userid(current_user["user_id"]).id
            campaign = Campaign(
                sponsor_id=sponsor_id,
                name=name,
                description=description,
                start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
                end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
                budget=budget,
                visibility=visibility,
                niche=CampaignNiche[niche].value
            )
            db.session.add(campaign)
            db.session.commit()
            return success(campaign.to_dict())
        except Exception as e:
            db.session.rollback()
            return internal_server_error(e)

    def __update_campaign(self, campaign_id):
        args = self.campaign_input_fields.parse_args()
        name = args['campaign_name']
        description = args['description']
        start_date = args['start_date']
        end_date = args['end_date']
        budget = args['budget']
        visibility = args['visibility']
        niche = args['niche']

        current_user = get_jwt()
        sponsor_id = SponsorAPI.get_sponsor_from_userid(current_user["user_id"]).id
        campaign = Campaign.query.filter_by(id=campaign_id, sponsor_id=sponsor_id).one()
        if not campaign:
            return resource_not_found("Campaign not found")

        try:
            campaign.name = name
            campaign.description = description
            campaign.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            campaign.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            campaign.budget = budget
            campaign.visibility = visibility
            campaign.niche = CampaignNiche[niche]
            db.session.commit()
            return success(campaign.to_dict())
        except Exception as e:
            db.session.rollback()
            return abort(f"some exception during transaction {e}")

    def __delete_campaign(self, campaign_id):
        campaign = Campaign.query.filter_by(id=campaign_id).first()
        if not campaign:
            return resource_not_found("Campaign not found")

        try:
            campaign.deleted_on = datetime.utcnow()
            db.session.commit()
            return create_response("Campaign deleted successfully", 200)
        except Exception as e:
            db.session.rollback()
            return abort(f"some exception during transaction {e}")

    def update_campaign_status(self, campaign_id):
        campaign = Campaign.query.filter_by(id=campaign_id).one()
        if not campaign:
            return resource_not_found("Campaign not found")

        data = request.get_json()
        status = data.get('status')

        if status not in CampaignStatus.__members__:
            return internal_server_error("Invalid status")

        campaign.status = CampaignStatus[status]
        db.session.commit()
        return success(campaign.status.name)

    @jwt_required()
    def get_campaign_analytics(self,campaign_id):
        campaign = Campaign.query.filter_by(id=campaign_id).first()
        if not campaign:
            return resource_not_found("Campaign not found")

        analytics = {
            "views": 1000,
            "clicks": 200,
            "engagement_rate": 20.0
        }
        return success({"data": analytics})

    @jwt_required()
    def get(self, sponsor_id=None, campaign_id=None):
        if campaign_id is not None:
            return self.__get_campaign_by_id(campaign_id)
        elif sponsor_id is not None:
            return self.__get_campaigns_by_sponsor(sponsor_id)
        else:
            return self.__get_all_campaigns()

    @jwt_required()
    @jwt_roles_required('sponsor')
    def post(self):
        return self.__create_campaign()

    @jwt_required()
    @jwt_roles_required('sponsor')
    def patch(self, campaign_id):
        return self.__update_campaign(campaign_id)

    @jwt_required()
    @jwt_roles_required('sponsor')
    def put(self, campaign_id):
        return self.update_campaign_status(campaign_id)

    @jwt_required()
    @jwt_roles_required('sponsor')
    def delete(self, campaign_id):
        return self.__delete_campaign(campaign_id)