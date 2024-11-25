from flask import render_template
from flask_restful import Resource

from services.tasks import send_html_email


class EmailAPI(Resource):

    def post(self):
        self.send_email()

    def send_email(self):
        subject = "the subject of the email"
        body = "the body of the email"
        address = "nitheshsenthil2303@gmail.com"
        msg_email = render_template("registration.html", body=body)
        send_html_email.delay(msg_email,address, subject,"nitheshkanna23@gmail.com")