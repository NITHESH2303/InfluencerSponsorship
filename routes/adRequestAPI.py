from datetime import datetime

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource, reqparse

from application import db
from application.models import Ads, Campaign, AdStatus
from application.response import success, internal_server_error, resource_not_found
from routes.decorators import jwt_roles_required


class AdRequestAPI(Resource):
    def __init__(self):
        self.adrequest_input_fields = reqparse.RequestParser()
        self.adrequest_input_fields.add_argument("campaign_id", type=int, required=True, help="Campaign ID is required.")
        self.adrequest_input_fields.add_argument("influencer_id", type=int, required=True, help="Influencer ID is required.")
        self.adrequest_input_fields.add_argument("requirement", type=str, required=True, help="Requirement is required.")
        self.adrequest_input_fields.add_argument("amount", type=int, required=True, help="Amount is required.")
        self.adrequest_input_fields.add_argument("negotiation_amount", type=int, help="Negotiation amount is required.")

        self.negotiation_input_fields = reqparse.RequestParser()
        self.negotiation_input_fields.add_argument("negotiation_amount", type=int, required=True, help="Negotiation amount is required.")

        self.adstatus_input_fields = reqparse.RequestParser()
        self.adstatus_input_fields.add_argument("status", type=str, required=True, help="Status is required.")

    def __validate_budget(self, campaign_id, ad_amount, ad_id=None):
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            raise ValueError(f"Campaign with ID {campaign_id} does not exist.")
        total_ad_cost = sum(ad.amount for ad in campaign.ads if not ad.deleted_on and (ad_id is None or ad.id != ad_id))
        if total_ad_cost + ad_amount > campaign.budget:
            raise ValueError(f"Ad amount exceeds the remaining budget of {campaign.budget - total_ad_cost}.")


    @jwt_required()
    def get(self, campaign_id=None, ad_id=None, influencer_id=None):
        def fetch_ads(query):
            ads = query.all()
            if not ads:
                return resource_not_found("No ad requests found.")
            return success([ad.to_dict(include=['sponsor_username', 'influencer_username']) for ad in ads])

        if campaign_id and ad_id:
            ad = Ads.query.filter_by(id=ad_id, campaign_id=campaign_id, deleted_on=None).first()
            if not ad:
                return resource_not_found()
            return success(ad.to_dict(include=['sponsor_username', 'influencer_username']))

        if campaign_id:
            return fetch_ads(Ads.query.filter_by(campaign_id=campaign_id, deleted_on=None))

        if influencer_id:
            return fetch_ads(Ads.query.filter_by(influencer_id=influencer_id, deleted_on=None))

        return resource_not_found("Invalid request parameters.")


    @jwt_required()
    @jwt_roles_required('sponsor')
    def post(self, influencer_id):
        args = self.adrequest_input_fields.parse_args()
        campaign_id = args['campaign_id']
        amount = args['amount']
        requirement = args['requirement']

        campaign = Campaign.query.filter_by(id=campaign_id).one()

        self.__validate_budget(campaign_id, amount)

        ad = Ads(
            campaign_id=campaign_id,
            sponsor_id=campaign.sponsor_id,
            influencer_id=influencer_id,
            amount=amount,
            requirement=requirement,
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
        amount = args['amount']
        requirement = args['requirement']
        ad = Ads.query.get(ad_id)
        if not ad:
            return resource_not_found()

        self.__validate_budget(ad.campaign_id, amount, ad.id)

        try:
            ad.amount = amount
            ad.requirement = requirement
            db.session.commit()
            return success(ad.to_dict())
        except Exception as e:
            db.session.rollback()
            return internal_server_error(f"An error occurred while updating the ad request: {e}")

    @jwt_required()
    @jwt_roles_required('influencer', 'sponsor')
    def patch(self, ad_id):
        endpoint = request.endpoint
        if endpoint == 'routes.accept_adrequest_negotiation':
            return self.__accept_negotiation(ad_id)
        elif endpoint == 'routes.update_adrequest_status':
            status_arg = self.adstatus_input_fields.parse_args()
            status = status_arg['status']
            if status == AdStatus.ACCEPTED.value:
                return self.__post_accept(ad_id)
            elif status == AdStatus.REJECTED.value:
                return self.__post_reject(ad_id)
            elif status == AdStatus.COMPLETED.value:
                return self.__mark_as_completed(ad_id)
        ad = Ads.query.get(ad_id)
        if not ad:
            return resource_not_found()

        args = self.negotiation_input_fields.parse_args()
        try:
            if args.get("negotiation_amount") is not None:
                ad.negotiation_amount = args["negotiation_amount"]
                ad.status = AdStatus.NEGOTIATION
            if args.get("requirement") is not None:
                ad.requirement = args["requirement"]
            db.session.commit()
            return success(ad.to_dict())
        except Exception as e:
            db.session.rollback()
            return internal_server_error(f"Failed to update the ad request with exception {e}. Please try again later.")

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


    def __post_accept(self, ad_id):
        ad = Ads.query.get(ad_id)
        if not ad:
            return resource_not_found()
        try:
            ad.status = AdStatus.ACCEPTED
            db.session.commit()
            return success(f"Ad request {ad_id} accepted.")
        except Exception as e:
            db.session.rollback()
            return internal_server_error(f"Error while accepting the ad request: {e}")


    def __post_reject(self, ad_id):
        ad = Ads.query.get(ad_id)
        if not ad:
            return resource_not_found()
        try:
            ad.status = AdStatus.REJECTED
            db.session.commit()
            return success(f"Ad request {ad_id} rejected.")
        except Exception as e:
            db.session.rollback()
            return internal_server_error(f"Error while rejecting the ad request: {e}")

    def __accept_negotiation(self, ad_id):
        ad = Ads.query.get_or_404(ad_id)
        if not ad.negotiation_amount:
            return resource_not_found("No negotiation amount to accept.")

        ad.amount = ad.negotiation_amount
        ad.status = AdStatus.ACCEPTED
        db.session.commit()
        return success("Negotiation accepted successfully.")

    def __mark_as_completed(self, ad_id):
        ad = Ads.query.get(ad_id)
        if not ad:
            return resource_not_found()
        try:
            ad.status = AdStatus.COMPLETED
            db.session.commit()
            return success(f"Ad request {ad_id} completed successfully.")
        except Exception as e:
            db.session.rollback()
            return internal_server_error(f"Error while completing the ad request: {e}")
