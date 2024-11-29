from flask import request
from flask_restful import Resource
from sqlalchemy import or_
from sqlalchemy.exc import NoResultFound

from application import db
from application.models import Sponsor, User
from application.response import success, create_response, resource_not_found
from routes.decorators import jwt_roles_required
from routes.emailAPI import EmailAPI
from routes.sponsor import SponsorAPI


class AdminOperationsAPI(Resource):

    @jwt_roles_required('admin')
    def get(self):
        endpoint = request.endpoint
        if endpoint == 'routes.list_flagged_users':
            return self.get_flagged_users()
        return self.__get_pending_sponsor_approvals()

    @jwt_roles_required('admin')
    def post(self, sponsor_id=None):
        endpoint = request.endpoint

        if endpoint == 'routes.flag_user':
            data = request.get_json()
            id = data.get('user_id')
            return self.flag_user(id)
        elif endpoint == 'routes.unflag_user':
            data = request.get_json()
            id = data.get('user_id')
            return self.unflag_user(id)
        return self.__change_sponsor_registration_status(sponsor_id)

    @staticmethod
    def __get_pending_sponsor_approvals():
        pending_sponsors = Sponsor.query.filter(or_(Sponsor.status == 0, Sponsor.status == 1)).all()
        sponsors = [sponsor.to_dict() for sponsor in pending_sponsors]
        return success(sponsors)

    @staticmethod
    def __change_sponsor_registration_status(sponsor_id):
        try:
            sponsor = Sponsor.query.filter_by(id=sponsor_id).one()
            if sponsor.status == SponsorAPI.sponsor_status['verified']:
                return create_response("Sponsor already approved", 400)
            if sponsor.status in SponsorAPI.status_transition:
                sponsor.status = SponsorAPI.status_transition[sponsor.status]
                db.session.commit()
                return create_response("Sponsor status updated successfully", 200, sponsor.to_dict())
            else:
                return create_response("Sponsor status cannot be changed", 400)
        except NoResultFound:
            return create_response("Sponsor not found", 404)
        except Exception as e:
            db.session.rollback()
            return create_response(f"An error occurred: {str(e)}", 500)

    @staticmethod
    def flag_user(user_id):
        reason = request.json.get('reason', None)
        user = User.query.get(user_id)
        if not user:
            return resource_not_found('User not found')
        user.is_flagged = True
        user.flag_reason = reason
        db.session.commit()
        EmailAPI.notify_flagged_user(user.email, reason)
        return success( f'User {user.username} flagged successfully')

    @staticmethod
    def unflag_user(user_id):
        user = User.query.get(user_id)
        if not user:
            return resource_not_found('User not found')
        user.is_flagged = False
        user.flag_reason = None
        db.session.commit()
        return success(f'User {user.username} unflagged successfully')

    @staticmethod
    def get_flagged_users():
        flagged_users = User.query.filter_by(is_flagged=True).all()
        data = [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'flag_reason': user.flag_reason,
                'role': 'Sponsor' if user.sponsor else 'Influencer',
            }
            for user in flagged_users
        ]
        return success(data)