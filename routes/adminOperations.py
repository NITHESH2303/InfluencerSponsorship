from flask_restful import Resource
from sqlalchemy import or_
from sqlalchemy.exc import NoResultFound

from application import db
from application.models import Sponsor
from application.response import success, create_response
from routes.decorators import class_roles_required


@class_roles_required('admin')
class AdminOperations(Resource):

    @staticmethod
    def get_pending_sponsor_approvals():
        pending_sponsors = Sponsor.query.filter(or_(Sponsor.status == 0, Sponsor.status == 1)).all()
        sponsors = [sponsor.name for sponsor in pending_sponsors]
        return success(sponsors)

    @staticmethod
    def change_sponsor_registration_status(sponsor_id):
        try:
            sponsor = Sponsor.query.filter_by(id=sponsor_id).one()
            if sponsor.status == Sponsor.sponsor_status['verified']:
                return create_response("sponsor already approved", 400)
            if sponsor.status in Sponsor.status_transition:
                sponsor.status = Sponsor.status_transition[sponsor.status]
            else:
                return create_response("Sponsor status cannot be changed", 400)
            db.session.commit()
            return create_response("Sponsor status updated successfully", 200, sponsor.to_dict())
        except NoResultFound:
            return create_response("Sponsor not found", 404)
        except Exception as e:
            return create_response(f"An error occurred: {str(e)}", 500)

    @staticmethod
    def reject_sponsor_registration(sponsor_id):
        try:
            sponsor = Sponsor.query.get_or_404(sponsor_id)
            db.session.delete(sponsor)
            db.session.commit()
            return create_response("Sponsor has been rejected", 201)
        except NoResultFound:
            return create_response("Sponsor not found", 404)
        except Exception as e:
            db.session.rollback()
            return create_response(f"An error occurred: {str(e)}", 500)





