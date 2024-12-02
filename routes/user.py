from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity, exceptions, verify_jwt_in_request, get_jwt
from flask_restful import reqparse, Resource
from sqlalchemy import exc

from application import User, db
from application.response import unauthorized, created, create_response, success, duplicate_entry, \
    internal_server_error
from validations.UserValidation import UserValidation


class UserAPI(Resource):
    def __init__(self):
        self.user_input_fields = reqparse.RequestParser()
        self.user_input_fields.add_argument("username", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("firstname", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("lastname", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("email", required=True, help="This field cannot be blank.")
        self.user_input_fields.add_argument("password", required=True, help="This field cannot be blank.")

        self.user_edit_fields = reqparse.RequestParser()
        self.user_edit_fields.add_argument("username", required=True, help="This field cannot be blank.")
        self.user_edit_fields.add_argument("first_name", required=True, help="This field cannot be blank.")
        self.user_edit_fields.add_argument("last_name", required=True, help="This field cannot be blank.")

    @jwt_required(optional=True)
    def get(self, user_id=None):
        endpoint = request.endpoint
        if endpoint == "routes.users_list":
            return self.__list_users()
        if endpoint == "routes.user_meta":
            return self.__get_user_meta()
        try:
            user = User.query.filter_by(id=user_id).one()
            if not user:
                return create_response("User not found", 404)

            try:
                verify_jwt_in_request(optional=True)
                current_user = get_jwt_identity()
            except exceptions.RevokedTokenError:
                current_user = None

            if current_user:
                return success(user.to_dict())

            else:
                return success(user.to_dict(exclude=['id', 'email', 'role']))

            # TODO : Implement private profile feature
            # if user.is_private:
            #     if user.fs_uniquifier != current_user:
            #         return create_response("This profile is private", 403)

        except Exception as e:
            return create_response(f"Error processing request with Exception : {e}", 500)

    def __list_users(self):
        users = User.query.all()
        all_users = [user.to_dict() for user in users if user.username != "admin"]
        return success(all_users)

    def __get_user_meta(self):
        current_user = get_jwt()
        if current_user:
            user_id = current_user["user_id"]
            user = User.query.filter_by(id=user_id).one()
            return success(user.to_dict())


    def post(self):
        args = self.user_input_fields.parse_args()
        username = args['username']
        first_name = args['firstname']
        last_name = args['lastname']
        email = args['email']
        password = args['password']

        UserValidation.check_for_existing_user(username, email)

        new_user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            # fs_uniquifier=str(uuid.uuid4())
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            return created(new_user.to_dict())
        except exc.IntegrityError as e:
            db.session.rollback()
            return duplicate_entry("User", e)

    # @jwt_required
    def patch(self):
        args = self.user_edit_fields.parse_args()
        username = args['username']
        first_name = args['first_name']
        last_name = args['last_name']

        try:
            user = User.query.filter_by(fs_uniquifier=get_jwt_identity()).one()
            updated_fields = {}

            fields = {
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            }

            for field, value in fields.items():
                if getattr(user, field) != value:
                    if field == "username":
                        if User.query.filter_by(username=value).first():
                            return duplicate_entry("UserName", error="")
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
