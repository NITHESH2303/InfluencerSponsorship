from flask import request
from flask_restful import Resource

from application.models import get_niches, get_AdStatus
from application.response import success


class EnumAPI(Resource):
    def get(self):
        endpoint = request.endpoint
        if endpoint == 'routes.list_niches':
            return success(get_niches())
        elif endpoint == 'routes.list_adstatus':
            return success(get_AdStatus())
