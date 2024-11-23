import uuid
from datetime import datetime
from sqlite3 import IntegrityError

from sqlalchemy import event

from application import User
from application.models import Ads, Campaign


def set_deleted_at(mapper, connection, target):
    if hasattr(target, 'deleted_on'):
        target.deleted_on = datetime.utcnow()
        target.deletion_count += 1
    else:
        if target.deleted_on is not None:
            target.restored_on = datetime.utcnow()


event.listen(User, 'before_update', set_deleted_at)

@event.listens_for(User, 'before_insert')
def generate_fs_uniquifier(mapper, connect, target):
    if not target.fs_uniquifier:
        target.fs_uniquifier = str(uuid.uuid4())

@event.listens_for(Ads, 'before_insert')
def validate_ad_budget(mapper, connection, target):
    campaign = Campaign.query.get(target.campaign_id)
    if not campaign:
        raise IntegrityError(None, None, f"Campaign with ID {target.campaign_id} does not exist.")

    total_ad_cost = sum(ad.amount for ad in campaign.ads if not ad.deleted_on)

    if total_ad_cost + target.amount > campaign.budget:
        raise ValueError(f"Cannot add this ad. Remaining budget: {campaign.budget - total_ad_cost}")

@event.listens_for(Ads, 'before_update')
def validate_ad_budget_update(mapper, connection, target):
    campaign = Campaign.query.get(target.campaign_id)
    if not campaign:
        raise IntegrityError(None, None, f"Campaign with ID {target.campaign_id} does not exist.")

    total_ad_cost = sum(ad.amount for ad in campaign.ads if not ad.deleted_on and ad.id != target.id)

    if total_ad_cost + target.amount > campaign.budget:
        raise ValueError(f"Cannot update this ad. Remaining budget: {campaign.budget - total_ad_cost}")
