from flask import request
from flask_restful import Resource

from application.response import internal_server_error, success
from routes.emailAPI import EmailAPI
from services.tasks import send_daily_reminders


class TriggerAPI(Resource):
    def post(self):
        endpoint = request.endpoint
        if endpoint == 'routes.trigger_daily_remainders':
            send_daily_reminders()
        try:
            result = [send_daily_reminders.delay(), EmailAPI.generate_reports_for_all_sponsors()]
            return success(result)
        except Exception as e:
            return internal_server_error(e)
