from datetime import datetime, timedelta

from flask import render_template
from flask_restful import Resource

from application.models import Sponsor
from services.tasks import send_html_email


class EmailAPI(Resource):

    def post(self):
        self.generate_reports_for_all_sponsors()

    def send_email(self):

        subject = "the subject of the email"
        body = "the body of the email"
        address = "nitheshsenthil2303@gmail.com"
        msg_email = render_template("registration.html", body=body)
        send_html_email.delay(msg_email,address, subject,"nitheshkanna23@gmail.com")

    def generate_reports_for_all_sponsors(self):
        today = datetime.utcnow()
        first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_day_last_month = (today.replace(day=1) - timedelta(days=1))

        sponsors = Sponsor.query.all()
        reports = []

        for sponsor in sponsors:
            report = sponsor.generate_monthly_report(first_day_last_month, last_day_last_month)
            reports.append(report)

            html_content = render_template('monthly_report.html', report=report)
            subject = f"Monthly Activity Report - {first_day_last_month.strftime('%B %Y')}"
            # recipient_email = sponsor.user.email

            send_html_email.delay(html_content, "nitheshsenthil2303@gmail.com", subject, "nitheshkanna23@gmail.com")

        return reports
