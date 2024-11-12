from datetime import datetime

from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt
from flask_restful import Resource,reqparse
from flask_security import roles_required

from application import db
from application.models import Sponsor, Campaign
from application.response import create_response, success


class CampaignsAPI(Resource):

    def __init__(self):
        self.campaign_input_fields = reqparse.RequestParser()
        self.campaign_input_fields.add_argument("name", type=str, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("description", type=str, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("start_date", type=datetime, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("end_date", type=datetime, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("budget", type=int, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("status", type=str, required=True, help="This field cannot be blank")
        self.campaign_input_fields.add_argument("visibility", type=int, help="This field cannot be blank")

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

    @jwt_required()
    @roles_required('Sponsor')
    def post(self):
        self.__create_campaign()

    @jwt_required()
    @roles_required('Sponsor')
    def put(self, campaign_id):
        self.__update_campaign(campaign_id)

    @jwt_required()
    @roles_required('Sponsor')
    def delete(self, campaign_id):
        self.__delete_campaign(campaign_id)


    def __create_campaign(self):
        args = self.campaign_input_fields.parse_args()
        sponsor_id = args['sponsor_id']
        name = args['name']
        description = args['description']
        start_date = args['start_date']
        end_date = args['end_date']
        budget = args['budget']
        status = args['status']
        visibility = args['visibility']
        try:
            new_campaign = Campaign(
                sponsor_id=sponsor_id,
                name=name,
                description=description,
                start_date=start_date,
                end_date=end_date,
                budget=budget,
                status=status,
                visibility=visibility
            )
            db.session.add(new_campaign)
            db.session.commit()
            return jsonify({"status": "success", "message": "Campaign created", "campaign": new_campaign.to_dict()}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 400

    def __update_campaign(self, campaign_id):
        args = self.campaign_input_fields.parse_args()
        sponsor_id = args['sponsor_id']
        name = args['name']
        description = args['description']
        start_date = args['start_date']
        end_date = args['end_date']
        budget = args['budget']
        status = args['status']
        visibility = args['visibility']
        campaign = Campaign.query.filter_by(id=campaign_id, sponsor_id=sponsor_id).first()
        if not campaign:
            return jsonify({"status": "error", "message": "Campaign not found"}), 404

        try:
            campaign.name = name
            campaign.description = description
            campaign.start_date = start_date
            campaign.end_date = end_date
            campaign.budget = budget
            campaign.status = status
            campaign.visibility = visibility
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
            db.session.delete(campaign)
            db.session.commit()
            return jsonify({"status": "success", "message": "Campaign deleted"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(e)}), 400