from flask_restful import reqparse, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import exc

from application import User, db
from application.response import unauthorized, created, create_response, success, duplicate_entry, internal_server_error
from validations.UserValidation import UserValidation


class UserAPI(Resource):
    def __init__(self):
        self.user_input_fields = reqparse.RequestParser()
        self.user_input_fields.add_argument("user_name", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("first_name", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("last_name", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("email", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("password", required=True, help="This field cannot be blank.")

    def get(self, user_id=None):
        current_user = get_jwt_identity()
        try:
            user = User.query.filter_by(fs_uniquifier=current_user).one() if current_user else User.query.get(user_id)
            if not user:
                return unauthorized()
            return user.to_dict(), 200
        except exc.NoResultFound:
            return unauthorized()

    def post(self):
        args = self.user_input_fields.parse_args()
        username = args['user_name']
        first_name = args['first_name']
        last_name = args['last_name']
        email = args['email']
        password = args['password']

        UserValidation.check_for_existing_user(username, email)

        new_user = User(
            user_name=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return created(new_user.to_dict())
        except exc.IntegrityError:
            db.session.rollback()
            return duplicate_entry("User")

    @jwt_required
    def put(self):
        args = self.user_input_fields.parse_args()
        user_name = args['user_name']
        first_name = args['first_name']
        last_name = args['last_name']

        try:
            user = User.query.filter_by(fs_uniquifier=get_jwt_identity()).one()
            updated_fields = {}

            fields = {
                "user_name": user_name,
                "first_name": first_name,
                "last_name": last_name,
            }

            for field, value in fields.items():
                if getattr(user, field) != value:
                    if field == "user_name":
                        if User.query.filter_by(user_name=value).first():
                            return duplicate_entry("UserName")
                    setattr(user, field, value)
                    updated_fields[field] = value

            if updated_fields:
                db.session.commit()
                return create_response("User details updated successfully.", 200, data=user.to_dict())
            else:
                return create_response("No changes made.", 204)

        except exc.NoResultFound:
            return unauthorized()

    @jwt_required
    def delete(self):
        try:
            current_user = get_jwt_identity()
            user = User.query.filter_by(fs_uniquifier=current_user()).one()
            user.is_deleted = True
            db.session.commit()
            return success("User deleted successfully.")
        except exc.NoResultFound:
            return create_response("User does not exist.", 404)
        except Exception as e:
            db.session.rollback()
            return internal_server_error(e)
