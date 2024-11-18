from datetime import datetime
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse, abort

from application import db
from application.models import Ads, Campaign
from application.response import success, internal_server_error, resource_not_found


class AdRequestAPI(Resource):
    def __init__(self):
        self.adrequest_input_fields = reqparse.RequestParser()
        self.adrequest_input_fields.add_argument("campaign_id", type=int, required=True, help="Campaign ID is required.")
        self.adrequest_input_fields.add_argument("influencer_id", type=int, required=True, help="Influencer ID is required.")
        self.adrequest_input_fields.add_argument("requirement", type=str, required=True, help="Requirement is required.")
        self.adrequest_input_fields.add_argument("amount", type=int, required=True, help="Amount is required.")

    def __validate_budget(self, campaign_id, ad_amount):
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            abort(404, message="Campaign not found.")

        total_cost = sum(ad.amount for ad in campaign.ads if ad.deleted_on is None)
        if total_cost + ad_amount > campaign.budget:
            abort(400, message=f"Ad cost exceeds the remaining campaign budget. Remaining budget: {campaign.budget - total_cost}.")

    @jwt_required()
    def get(self):
        campaign_id = request.args.get("campaign_id", type=int)
        ad_id = request.args.get("ad_id", type=int)

        if campaign_id and ad_id:
            ad = Ads.query.filter_by(id=ad_id, campaign_id=campaign_id).first()
            if not ad:
                return resource_not_found()
            return success(ad.to_dict())

        elif campaign_id:
            ads = Ads.query.filter_by(campaign_id=campaign_id, deleted_on=None).all()
            if not ads:
                return resource_not_found("No ad requests found for this campaign.")
            return success([ad.to_dict() for ad in ads])

        return resource_not_found("Invalid request parameters.")

    @jwt_required()
    def post(self):
        args = self.adrequest_input_fields.parse_args()
        self.__validate_budget(args["campaign_id"], args["amount"])

        ad = Ads(
            campaign_id=args["campaign_id"],
            influencer_id=args["influencer_id"],
            request=args["request"],
            amount=args["amount"],
            requirement=args["requirement"],
        )
        try:
            db.session.add(ad)
            db.session.commit()
            return success(ad.to_dict())
        except Exception as e:
            db.session.rollback()
            return internal_server_error(f"An error occurred while creating the ad request: {e}")

    @jwt_required()
    def put(self, ad_id):
        args = self.adrequest_input_fields.parse_args()
        ad = Ads.query.get(ad_id)
        if not ad:
            return resource_not_found()

        self.__validate_budget(ad.campaign_id, args["amount"] - ad.amount)

        try:
            ad.request = args["request"]
            ad.amount = args["amount"]
            ad.requirement = args["requirement"]
            db.session.commit()
            return success(ad.to_dict())
        except Exception as e:
            db.session.rollback()
            return internal_server_error(f"An error occurred while updating the ad request: {e}")

    @jwt_required()
    def patch(self, ad_id):
        ad = Ads.query.get(ad_id)
        if not ad:
            return resource_not_found()

        args = self.adrequest_input_fields.parse_args()
        try:
            ad.amount = args.get("amount", ad.amount)
            ad.requirement = args.get("requirement", ad.requirement)
            ad.status = "Pending"  # Reset status for negotiation
            db.session.commit()
            return success(ad.to_dict())
        except Exception as e:
            db.session.rollback()
            return internal_server_error(f"An error occurred while negotiating the ad request: {e}")

    @jwt_required()
    def delete(self, ad_id):
        ad = Ads.query.get(ad_id)
        if not ad:
            return resource_not_found()

        try:
            ad.deleted_on = datetime.utcnow()
            db.session.commit()
            return success("Ad request deleted successfully.")
        except Exception as e:
            db.session.rollback()
            return internal_server_error(f"An error occurred while deleting the ad request: {e}")
