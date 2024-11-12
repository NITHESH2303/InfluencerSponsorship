from importlib.resources import Resource

from flask_jwt_extended import jwt_required
from flask_restful import reqparse
from flask_security import roles_required


class AdRequestAPI(Resource):
    def __init__(self):
        self.adrequest_input_fields = reqparse.RequestParser()
        self.adrequest_input_fields.add_argument("requirement", type=str)
        self.adrequest_input_fields.add_argument("amount", type=int, required=True)
        self.adrequest_input_fields.add_argument("status", type=str, required=True)

    @jwt_required()
    @roles_required('sponsor')
    def get(self):
        self.__create_adrequest()
