from flask_restful import Resource, reqparse
from flask_security.utils import verify_password
from flask_jwt_extended import create_access_token
from sqlalchemy import exc
import re

from application.models import User
from application.response import *


class AuthAPI(Resource):

    def __init__(self):
        self.auth_input_fields = reqparse.RequestParser()
        self.auth_input_fields.add_argument("identifier", type=str, required=True, help="Enter Your User Or Email")
        self.auth_input_fields.add_argument("password", type=str, required=True, help="Password is required")

    def get(self):
        return

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
