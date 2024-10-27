from flask_restful import Resource, reqparse

from application import db
from application.models import Sponsor
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

    def sponsor_registration(self):
        args = self.sponsor_input_fields.parse_args()
        company_name = args["company_name"]
        industry_type = args["industry_type"]
        description = args["description"]

        new_sponsor = Sponsor(
            company_name = company_name,
            industry_type = industry_type,
            description = description
        )

        try:
            db.session.add(new_sponsor)
            db.session.commit()
            return success(new_sponsor.to_dict())
        except Exception as e:
            db.session.rollback()
            return internal_server_error(e)




