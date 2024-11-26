from flask import request
from flask_restful import Resource

from services.tasks import send_daily_reminders


class TriggerAPI(Resource):
    def post(self):
        endpoint = request.endpoint
        if endpoint == 'routes.trigger_daily_remainders':
            send_daily_reminders()
