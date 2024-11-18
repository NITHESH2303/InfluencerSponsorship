from datetime import datetime

from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from flask_restful import Resource, reqparse

from application import db
from application.models import Sponsor, Campaign, AdStatus
from application.response import create_response, success, internal_server_error
from routes.decorators import jwt_roles_required
from routes.sponsor import SponsorAPI


class CampaignsAPI(Resource):

    def __init__(self):
        self.campaign_input_fields = reqparse.RequestParser()
        self.campaign_input_fields.add_argument("name", type=str, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("description", type=str, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("start_date", type=str, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("end_date", type=str, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("budget", type=int, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("visibility", type=str, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("niche", type=str, required=True, help="This field cannot be blank")

    @staticmethod
    def __get_campaigns_by_sponsor(sponsor_id=None):
        if sponsor_id is None:
            current_user = get_jwt()
            sponsor_id = current_user["user_id"]
        sponsor = Sponsor.query.filter_by(id=sponsor_id).first()

        if not sponsor:
            return create_response("Sponsor not found", 404)

        campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
        campaign_list = [campaign.to_dict() for campaign in campaigns]
        return success(campaign_list)

    @staticmethod
    def __get_all_campaigns():
        campaigns = Campaign.query.all()
        all_campaigns = [campaign.to_dict() for campaign in campaigns]
        return success(all_campaigns)

    def __create_campaign(self):
        args = self.campaign_input_fields.parse_args()
        name = args['name']
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
                niche=niche
            )
            db.session.add(campaign)
            db.session.commit()
            return success(campaign.to_dict())
        except Exception as e:
            db.session.rollback()
            return internal_server_error(e)

    def __update_campaign(self, campaign_id):
        args = self.campaign_input_fields.parse_args()
        sponsor_id = args['sponsor_id']
        name = args['name']
        description = args['description']
        start_date = args['start_date']
        end_date = args['end_date']
        budget = args['budget']
        visibility = args['visibility']
        niche = args['niche']
        campaign = Campaign.query.filter_by(id=campaign_id, sponsor_id=sponsor_id).first()
        if not campaign:
            return jsonify({"status": "error", "message": "Campaign not found"}), 404

        try:
            campaign.name = name
            campaign.description = description
            campaign.start_date = start_date
            campaign.end_date = end_date
            campaign.budget = budget
            campaign.visibility = visibility
            campaign.niche = niche
            db.session.commit()
            return jsonify({"status": "success", "message": "Campaign updated", "campaign": campaign.to_dict()}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 400

    def __delete_campaign(self, campaign_id):
        campaign = Campaign.query.filter_by(id=campaign_id).first()
        if not campaign:
            return jsonify({"status": "error", "message": "Campaign not found"}), 404

        try:
            campaign.deleted_on = datetime.utcnow()
            db.session.commit()
            return create_response("Campaign deleted sucessufully", 200)
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 400

    @jwt_roles_required('sponsor')
    def update_campaign_status(self, campaign_id):
        campaign = Campaign.query.filter_by(id=campaign_id).one()
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        data = request.get_json()
        status = data.get('status')

        if status not in AdStatus.__members__:
            return jsonify({"error": "Invalid status"}), 400

        campaign.status = AdStatus[status]
        db.session.commit()
        return jsonify({"message": "Campaign status updated", "status": campaign.status.name})

    @jwt_required()
    def get_campaign_analytics(self,campaign_id):
        campaign = Campaign.query.filter_by(id=campaign_id).first()
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404

        analytics = {
            "views": 1000,
            "clicks": 200,
            "engagement_rate": 20.0
        }
        return jsonify({"data": analytics})

    @jwt_required()
    def get(self, sponsor_id=None):
        # sponsor_id = request.args.get("sponsor_id")

        if sponsor_id:
            return self.__get_campaigns_by_sponsor(sponsor_id)
        return self.__get_all_campaigns()

    @jwt_required()
    @jwt_roles_required('sponsor')
    def post(self):
        return self.__create_campaign()

    @jwt_required()
    @jwt_roles_required('sponsor')
    def put(self, campaign_id):
        return self.__update_campaign(campaign_id)

    @jwt_required()
    @jwt_roles_required('sponsor')
    def delete(self, campaign_id):
        return self.__delete_campaign(campaign_id)