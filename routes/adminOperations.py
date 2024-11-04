from flask_restful import Resource
from flask_security import roles_required
from sqlalchemy import or_
from sqlalchemy.exc import NoResultFound

from application import db
from application.models import Sponsor
from application.response import success, create_response


class AdminOperations(Resource):

    @roles_required('admin')
    def get(self):
        return self.__get_pending_sponsor_approvals()

    @roles_required('admin')
    def post(self, sponsor_id):
        return self.__change_sponsor_registration_status(sponsor_id)

    @staticmethod
    def __get_pending_sponsor_approvals():
        pending_sponsors = Sponsor.query.filter(or_(Sponsor.status == 0, Sponsor.status == 1)).all()
        sponsors = [sponsor.name for sponsor in pending_sponsors]
        return success(sponsors)

    @staticmethod
    def __change_sponsor_registration_status(sponsor_id):
        try:
            sponsor = Sponsor.query.filter_by(id=sponsor_id).one()
            if sponsor.status == Sponsor.sponsor_status['verified']:
                return create_response("Sponsor already approved", 400)
            if sponsor.status in Sponsor.status_transition:
                sponsor.status = Sponsor.status_transition[sponsor.status]
            else:
                return create_response("Sponsor status cannot be changed", 400)
            db.session.commit()
            return create_response("Sponsor status updated successfully", 200, sponsor.to_dict())
        except NoResultFound:
            return create_response("Sponsor not found", 404)
        except Exception as e:
            db.session.rollback()  # Rollback on error
            return create_response(f"An error occurred: {str(e)}", 500)