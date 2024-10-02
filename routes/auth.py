from flask_restful import Resource, reqparse
from flask_security import verify_password, auth_required, current_user
from flask_jwt_extended import create_access_token
from sqlalchemy import exc
import re

from application.database import db
from application.models import User
from application.response import *


class AuthAPI(Resource):

    def __init__(self):
        self.auth_input_fields = reqparse.RequestParser()
        self.auth_input_fields.add_argument("identifier", type=str, required=True, help="Enter Your User Or Email")
        self.auth_input_fields.add_argument("password", type=str, required=True, help="Password is required")

    @auth_required()
    def get(self):
        try:
            user_data = current_user.to_dict(exclude=None)
            return user_data
        except exc.NoResultFound:
            return unauthorized()

    @auth_required()
    def put(self):
        args = self.auth_input_fields.parse_args()
        identifier = args["identifier"]
        password = args["password"]
        try:
            if not verify_password(password, current_user.password):
                return validation_error("Incorrect Password")
            if identifier:
                if '@' in identifier and re.match(r"[^@]+@[^@]+\.[^@]+", identifier):
                    current_user.email = identifier
                else:
                    current_user.username = identifier
                db.session.commit()
                return create_response("Username/Email updated successfully", 200)
        except Exception as e:
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
            if verify_password(password, user.password):
                token = create_access_token(identity=user.fs_uniquifier, fresh=True)
                user_data = user.to_dict(exclude=None)
                response = {
                    "token": token,
                    "user": user_data
                }
                return create_response("Login successful", 200, response)
            else:
                return validation_error("Incorrect Password")
