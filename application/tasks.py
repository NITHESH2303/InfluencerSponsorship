from flask import current_app
from application.celery_app import celery
from application.database import db
from application.models import Influencer
from application.utils import get_follower_count
from application.mail import mail

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
def send_remainders():
    users = db.session.query(User, Role).filter(Role.name = "influencer").all()
    for user in users:
        pendingAds = Ads.query.filter_by(influencer_id = user.user_id)
        if pendingAds:
            msg = Message(sender="noufal24rahman@gmail.com", recipients=[user.email], subject="Time to check ad requests! | Influencer app")
            msg.html = render_template("remainder.html", name = user.name)
            mail.send(msg)
    return {'task': 'remainders'}

@celery.task()
def export_content(user_id):
    data = CampaignsAPI.__get_all_campaigns()
    mail_template = render_template('export.html', user = data)
    msg = Message(sender="nithesh.kanna@zohocorp.com", recipients=[data['email']], subject="Export content | Blog Lite")
    msg.html = mail_template
    msg.attach("blog_lite_export_{}.json".format(user_id), 'application/json', json.dumps(data, indent=2))
    mail.send(msg)
    return {"name": data['name'], "email": data['email'], "task": "export"}

@celery.on_after_finalize.connect
def schedule_tasks(sender, **kwargs):
    # TODO: change time to suit needds
    sender.add_periodic_task(50.0, send_remainders.s(), name="Send daily report")