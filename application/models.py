from datetime import datetime
from enum import Enum
from sqlite3 import IntegrityError

from flask import current_app
from flask_security import verify_password, hash_password, UserMixin, RoleMixin
from sqlalchemy.orm import validates

from application.database import db
from routes.Reports import ReportsAPI
from validations.RoleValidations import RoleValidations


class Model(db.Model):
    __abstract__ = True

    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdStatus(Enum):
    PENDING = 'Pending'
    NEGOTIATION = 'Negotiation'
    ACCEPTED = 'Accepted'
    REJECTED = 'Rejected'
    COMPLETED = 'Completed'

def get_AdStatus():
    adstatus = [status.value for status in AdStatus]
    return adstatus

class CampaignStatus(Enum):
    YetToStart = 'YetToStart'
    Active = 'Active'
    Completed = 'Completed'

class CampaignNiche(Enum):
    Technology = 'Technology'
    Fashion = 'Fashion'
    Fitness = 'Fitness'
    Food = 'Food'
    Travel = 'Travel'
    Education = 'Education'

def get_niches():
    niches = [niche.value for niche in CampaignNiche]
    return niches

class UserRoles(Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'))
    roleid = db.Column(db.Integer, db.ForeignKey('role.id'))


class Role(Model, RoleMixin):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.String(255), unique=True)


class User(Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String)
    email = db.Column(db.String, unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String, nullable=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    image = db.Column(db.String, nullable=True)
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_on = db.Column(db.DateTime, default=None)
    restored_on = db.Column(db.DateTime, default=None)
    deletion_count = db.Column(db.Integer, default=0)
    is_flagged = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.String, default=None)
    influencer = db.relationship('Influencer', back_populates='user', foreign_keys='Influencer.userid', uselist=False)
    sponsor = db.relationship('Sponsor', back_populates='user', foreign_keys='Sponsor.userid', uselist=False)


    def add_role(self, role):
        current_roles = self.get_cached_role_names()
        RoleValidations.validate_role_assignment(current_roles, role)
        new_role = Role.query.filter_by(name=role).first()
        if new_role:
            self.role.append(new_role)
            self.invalidate_role_cache()
        else:
            raise ValueError('Role with name "{}" does not exist'.format(role))

    def get_cached_role_names(self):
        cached_roles = current_app.redis_client.get(f'user_roles:{self.id}')

        if cached_roles:
            return cached_roles.split(',')
        else:
            role_names = [role.name for role in self.role]
            current_app.redis_client.set(f'user_roles:{self.id}', ','.join(role_names), ex=3600)
            return role_names

    def invalidate_role_cache(self):
        current_app.redis_client.delete(f'user_roles:{self.id}')

    def verify_password(self, password):
        return verify_password(password, self.password_hash)

    def set_password(self, password):
        self.password_hash = hash_password(password)

    def to_dict(self, exclude=None):
        exclude = exclude or []
        data = {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "image": self.image,
            "role": [role.name for role in self.roles],
            "influencer_id": self.influencer.id if self.influencer else None,
            "sponsor_id": self.sponsor.id if self.sponsor else None
        }
        return {key: val for key, val in data.items() if key not in exclude}


class Sponsor(Model):
    __tablename__ = 'sponsor'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE', name='fk_sponsor_userid'), nullable=False)
    username = db.Column(db.String, db.ForeignKey('user.username', ondelete='CASCADE', name='fk_sponsor_username'), nullable=False)
    company_name = db.Column(db.String, nullable=False)
    industry_type = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    status = db.Column(db.Integer, default=0)
    campaigns = db.relationship('Campaign', backref='sponsor', lazy=True)
    user = db.relationship('User', back_populates='sponsor', foreign_keys=[userid])

    def generate_monthly_report(self, start_date, end_date):
        return ReportsAPI.generate_sponsor_monthly_report(self, start_date, end_date)

    def to_dict(self, exclude=None):
        exclude = exclude or []
        data = {
            "sponsorid" : self.id,
            "user_id": self.userid,
            "username": self.username,
            "company_name": self.company_name,
            "industry_type": self.industry_type,
            "description": self.description,
            "verification_status": self.status,
        }
        return {key: val for key, val in data.items() if key not in exclude}



class Influencer(Model):
    __tablename__ = 'influencer'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE', name='fk_influencer_userid'), nullable=False)
    username = db.Column(db.String, db.ForeignKey('user.username', ondelete='CASCADE', name='fk_influencer_username'), nullable=False)
    social_media_profiles = db.relationship('SocialMediaProfile', backref='influencer', lazy=True, cascade="all, delete-orphan")
    about = db.Column(db.String, default="")
    followers = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String, nullable=False)
    ads = db.relationship('Ads', backref='influencer', lazy=True)
    user = db.relationship('User', back_populates='influencer', foreign_keys=[userid])

    def to_dict(self, exclude=None):
        exclude = exclude or []
        data = {
            "influencer_id": self.id,
            "user_id": self.userid,
            "username": self.username,
            "social_media_profiles": [
                {
                    "platform": profile.platform,
                    "username": profile.username,
                    "followers": profile.followers,
                }
                for profile in self.social_media_profiles
            ],
            "about": self.about,
            "category": self.category,
            "followers": self.followers,
            "is_flagged": self.user.is_flagged,
            "flag_reason": self.user.flag_reason,
            "ads": [ {
                "ad_id": ad.id,
                "campaign_id": ad.campaign_id,
                "sponsor_id": ad.sponsor_id,
                "requirement": ad.requirement,
                "amount": ad.amount,
                "status": ad.status.value,
                "campaign_name": ad.campaign.name
            } for ad in self.ads if ad.deleted_on is None ]
        }
        return {key: val for key, val in data.items() if key not in exclude}


class SocialMediaProfile(Model):
    __tablename__ = 'social_media_profile'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id', ondelete='CASCADE'), nullable=False)
    platform = db.Column(db.String, nullable=False)
    followers = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('platform', 'username', name='uq_platform_username'),
    )


class Campaign(Model):
    __tablename__ = 'campaign'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(CampaignStatus), default=CampaignStatus.YetToStart)
    visibility = db.Column(db.Boolean, nullable=False, default=False)
    niche = db.Column(db.Enum(CampaignNiche), nullable=False)
    ads = db.relationship('Ads', backref='campaign', lazy=True)
    deleted_on = db.Column(db.DateTime, nullable=True)

    def to_dict(self, exclude=None):
        exclude = exclude or []
        spent_amount = sum(ad.amount for ad in self.ads if ad.deleted_on is None)
        remaining_budget = self.budget - spent_amount
        current_date = datetime.utcnow()
        total_duration = (self.end_date - self.start_date).days
        elapsed_duration = (current_date - self.start_date).days if current_date > self.start_date else 0
        progress_percentage = min(100, max(0, (elapsed_duration / total_duration) * 100)) if total_duration > 0 else 0
        data = {
            "campaign_id": self.id,
            "sponsor_id": self.sponsor_id,
            "campaign_name": self.name,
            "description": self.description,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "budget": self.budget,
            "status": self.status.value,
            "visibility": self.visibility,
            "niche": self.niche.value,
            "spent_amount": spent_amount,
            "remaining_budget": remaining_budget,
            "progress_percentage": progress_percentage
        }
        return {key: val for key, val in data.items() if key not in exclude}


class Ads(Model):
    __tablename__ = 'ads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'))
    status = db.Column(db.Enum(AdStatus), default=AdStatus.PENDING)
    amount = db.Column(db.Integer, nullable=False)
    negotiation_amount = db.Column(db.Integer, nullable=True)
    requirement = db.Column(db.String, nullable=False)
    messages = db.Column(db.String)
    deleted_on = db.Column(db.DateTime, nullable=True)

    @validates('amount')
    def validate_amount(self, key, value):
        campaign = Campaign.query.get(self.campaign_id)
        if not campaign:
            raise IntegrityError(None, None, f"Campaign with ID {self.campaign_id} does not exist.")

        total_ad_cost = sum(ad.amount for ad in campaign.ads if not ad.deleted_on and (self.id is None or ad.id != self.id))

        if total_ad_cost + value > campaign.budget:
            raise ValueError(f"Ad amount exceeds the remaining budget of {campaign.budget - total_ad_cost}.")

        return value



    def to_dict(self, include=None, exclude=None):
        include = include or []
        exclude = exclude or []
        data = {
            "ad_id": self.id,
            "campaign_id": self.campaign_id,
            "sponsor_id": self.sponsor_id,
            "influencer_id": self.influencer_id,
            "status": self.status.value,
            "amount": self.amount,
            "negotiation_amount": self.negotiation_amount,
            "requirement": self.requirement,
            "messages": self.messages,
        }
        if 'campaign_name' in include:
            campaign = Campaign.query.get(self.campaign_id)
            data['campaign_name'] = campaign.name if campaign else None
        if 'sponsor_username' in include:
            sponsor = Sponsor.query.get(self.sponsor_id)
            data['sponsor_username'] = sponsor.username if sponsor else None
        if 'influencer_username' in include:
            influencer = Influencer.query.get(self.influencer_id)
            data['influencer_username'] = influencer.username if influencer else None
        return {key: val for key, val in data.items() if key not in exclude}
