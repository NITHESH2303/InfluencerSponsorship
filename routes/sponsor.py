from datetime import datetime
from sqlite3 import IntegrityError

from flask import current_app, request
from flask_jwt_extended import get_jwt, jwt_required
from flask_restful import Resource, reqparse, abort

from application import db
from application.models import Sponsor, User, Role
from application.response import success, internal_server_error


class SponsorAPI(Resource):

    sponsor_status = {
        "not_verified": 0,
        "verification_initiated" : 1,
        "verified" : 2
    }
    status_transition = {
        sponsor_status["not_verified"]: sponsor_status["verification_initiated"],
        sponsor_status["verification_initiated"]: sponsor_status["verified"]
    }


    def __init__(self):
        self.sponsor_input_fields = reqparse.RequestParser()
        self.sponsor_input_fields.add_argument("company_name", type=str, required=True, help="Company name")
        self.sponsor_input_fields.add_argument("industry_type", type=str, required=True, help="Industry type")
        self.sponsor_input_fields.add_argument("description", type=str, help="description")

    @jwt_required()
    def get(self, sponsor_id=None):
        return self.__get_sponsor_details(sponsor_id)

    @jwt_required()
    def post(self):
        return self.__sponsor_registration()

    @jwt_required()
    def __sponsor_registration(self):
        args = self.sponsor_input_fields.parse_args()
        company_name = args["company_name"]
        industry_type = args["industry_type"]
        description = args["description"]

        current_user = get_jwt()
        userid = current_user['user_id']
        username = current_user['username']

        sponsor_role = Role.query.filter_by(name="sponsor").one_or_none()
        user = User.query.filter_by(username=username, id=userid).one()

        if sponsor_role not in user.roles:
            user.roles.append(sponsor_role)
        else:
            abort(400, message=f"Role {sponsor_role.name} already assigned to {username}.")

        new_sponsor = Sponsor(
            userid=userid,
            username=username,
            company_name=company_name,
            industry_type=industry_type,
            description=description,
            status=SponsorAPI.sponsor_status["not_verified"]
        )

        try:
            db.session.add(new_sponsor)
            db.session.commit()
            return success(new_sponsor.to_dict())
        except IntegrityError:
            db.session.rollback()
            return internal_server_error("Sponsor with this information already exists.")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error occurred during sponsor registration: {e}")
            return internal_server_error("An error occurred while processing your request.")

    def __get_sponsor_details(self, sponsor_id):
        if sponsor_id is None:
            endpoint = request.endpoint
            if endpoint == 'routes.sponsor_list':
                return self.__get_sponsor_list()
            return self.__get_sponsor_meta()
        sponsor = Sponsor.query.filter_by(id=sponsor_id).one()
        user = User.query.get(sponsor.userid)
        current_date = datetime.now()
        campaigns = [{
            "id": c.id,
            "name": c.name,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "progress_percentage": (
                lambda total_duration, elapsed_duration:
                min(100, max(0, (elapsed_duration / total_duration) * 100)) if total_duration > 0 else 0
            )(
                (c.end_date - c.start_date).days,
                (current_date - c.start_date).days if current_date > c.start_date else 0
            )
        } for c in sponsor.campaigns if c.deleted_on is None]

        return success({
            "userid": user.id,
            "username": sponsor.username,
            "company_name": sponsor.company_name,
            "industry_type": sponsor.industry_type,
            "description": sponsor.description,
            "email": user.email,
            "verification_status": sponsor.status,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "campaigns": campaigns,
        })

    def __get_sponsor_meta(self):
        current_user = get_jwt()
        sponsor = Sponsor.query.filter_by(userid=current_user['user_id']).one()
        sponsor_data = sponsor.to_dict()
        return success(sponsor_data)

    def __get_sponsor_list(self):
        sponsors = Sponsor.query.all()
        sponsors_list = [sponsor.to_dict() for sponsor in sponsors]
        return success(sponsors_list)

    @staticmethod
    def get_sponsor_from_userid(userid):
        sponsor = Sponsor.query.filter_by(userid=userid).one()
        return sponsor

