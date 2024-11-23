from flask_restful import Resource

from application.models import get_niches
from application.response import success


class Niches(Resource):
    def get(self):
        return success(get_niches())