import re

from flask import current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from flask_restful import Resource, reqparse
from flask_security import verify_password
from sqlalchemy import exc

from application.database import db
from application.event_listeners import *
from application.response import *


class AuthAPI(Resource):

    def __init__(self):
        self.auth_input_fields = reqparse.RequestParser()
        self.auth_input_fields.add_argument("identifier", type=str, required=True, help="Enter Your User Or Email")
        self.auth_input_fields.add_argument("password", type=str, required=True, help="Password is required")
        self.auth_input_fields.add_argument("new_password", type=str, help="Enter your new password")

    @jwt_required()
    def get(self):
        try:
            current_user_identity = get_jwt_identity()
            user_data = User.query.filter_by(fs_uniquifier=current_user_identity).one()
            return user_data.to_dict(exclude=None)
        except exc.NoResultFound:
            return unauthorized()

    @jwt_required()
    def put(self):
        args = self.auth_input_fields.parse_args()
        identifier = args["identifier"]
        password = args["password"]
        new_password = args["new_password"]
        try:
            user = User.query.filter_by(fs_uniquifier=get_jwt_identity()).one()
            if not verify_password(password, user.password_hash):
                return validation_error("Incorrect Password")
            if identifier:
                existing_user = User.query.filter_by(email=identifier).first()
                if existing_user:
                    return validation_error("Email Already Exists")
                else:
                    if '@' in identifier and re.match(r"[^@]+@[^@]+\.[^@]+", identifier):
                        user.email = identifier
                    else:
                        return validation_error("Invalid Email")
                    return create_response("Email updated successfully", 200)

            if new_password:
                user.password_hash = user.set_password(new_password)

            db.session.commit()
            return create_response("Password updated successfully", 200)
        except exc.NoResultFound:
            return unauthorized()
        except Exception as e:
            db.session.rollback()
            return forbidden()

    def post(self):
        global inp_type
        args = self.auth_input_fields.parse_args()
        identifier = args.get('identifier')
        password = args.get('password')
        try:
            if '@' in identifier and re.match(r"[^@]+@[^@]+\.[^@]+", identifier):
                inp_type = "email"
                user = User.query.filter_by(email=identifier).one()
            else:
                inp_type = "user"
                user = User.query.filter_by(username=identifier).one()
        except exc.NoResultFound:
            return user_not_found(identifier, inp_type)
        else:
            if verify_password(password, user.password_hash):
                user_roles = user.role
                access_token = create_access_token(identity=user.fs_uniquifier, additional_claims={"role": user_roles})
                refresh_token = create_refresh_token(identity=user.fs_uniquifier)
                user_data = user.to_dict(exclude=None)
                response = {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": user_data
                }
                return create_response("Login successful", 200, response)
            else:
                return validation_error("Incorrect Password")

    @jwt_required(refresh=True)
    def patch(self):
        current_user_identity = get_jwt_identity()
        new_access_token = create_access_token(identity=current_user_identity)
        return create_response("Token refreshed successfully", 200, {"access_token": new_access_token})

    @jwt_required(refresh=True)
    def delete(self):
        jti = get_jwt()["jti"]
        self.add_token_to_blacklist(jti, expires_in=300)
        return create_response("Successfully logged out", 200)

    def add_token_to_blacklist(self, jti, expires_in):
        redis_client = current_app.redis_client
        redis_client.setex(f"blacklist:{jti}", expires_in, 'true')
