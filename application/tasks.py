from flask import current_app
from application.celery_app import celery
from application.database import db
from application.models import Influencer
from application.utils import get_follower_count

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
