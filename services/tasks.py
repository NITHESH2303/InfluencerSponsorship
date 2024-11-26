import base64
import os
from email.mime.text import MIMEText

import httplib2shim
from flask import current_app
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from sqlalchemy import and_

from application.database import db
from application.models import Influencer, AdStatus, Ads, Sponsor
from application.response import internal_server_error
from application.utils import get_follower_count
from services.celery_app import celery
from token_gen import SCOPES

celery.conf.timezone = 'Asia/Kolkata'

@celery.task()
def update_follower_counts(influencer_id):
    with celery.app.app_context():
        influencer = Influencer.query.get(influencer_id)
        if not influencer:
            return

        total_followers = 0
        for profile in influencer.social_media_profiles:
            profile.followers_count = get_follower_count(profile.platform)
            total_followers += profile.followers_count

        influencer.followers = total_followers
        db.session.commit()

        redis_key = f"influencer:{influencer_id}:followers"
        current_app.redis_client.set(redis_key, total_followers, ex=3600)

@celery.task()
def update_all_influencers_follower_counts():
    with current_app.app_context():
        influencers = Influencer.query.all()
        for influencer in influencers:
            update_follower_counts.delay(influencer.id)

@celery.task()
def send_daily_reminders():
    influencers = Influencer.query.all()
    for influencer in influencers:
        try:
            pendingAds = Ads.query.filter(
                and_(Ads.influencer_id == influencer.id, Ads.status == AdStatus.PENDING)).all()
            if pendingAds:
                subject = "Daily Reminder: Check Your Pending Ads"
                email_body = f"""
                Hi {influencer.username},

                You have pending ad requests awaiting your action.
                Visit your dashboard to view and accept these requests.

                Or, check out the public ad requests to find new opportunities.
                """
                send_html_email.delay(email_body, "nitheshsenthil2303@gmail.com", subject, "nitheshkanna23@gmail.com")
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            return internal_server_error(e)

    # return {'task': 'remainders'}


@celery.task
def send_monthly_reports():
    Sponsor.generate_reports_for_all_sponsors()

@celery.task()
def send_html_email(body, email, subject, sender):

    httplib2shim.patch()
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)

    sender = sender
    to = email
    message_Text = body
    msg = create_message(sender,email,subject,message_Text)
    send_message(service,"me",msg)

def send_message(service, user_id, message):
    """Send an email message.
    Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    message: Message to be sent.
    Returns:
    Sent Message.
    """
    try:
        message = (service.users().messages().send(userId=user_id, body=message)
                   .execute())
        print ('Message Id: %s' % message['id'])
        return message
    except Exception as error:
        print ('An error occurred: %s' % error)


def create_message(sender, to, subject, message_text):
    """Create a message for an email.
    Args:
      sender: Email address of the sender.
      to: Email address of the receiver.
      subject: The subject of the email message.
      message_text: The text of the email message.
    Returns:
      An object containing a base64url encoded email object.
    """
    message = MIMEText(message_text,"html")
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    b64_bytes = base64.urlsafe_b64encode(message.as_bytes())
    b64_string = b64_bytes.decode()
    return {'raw': b64_string}