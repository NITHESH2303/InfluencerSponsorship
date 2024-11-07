from datetime import datetime
from enum import Enum

from flask import current_app
from flask_security import verify_password, hash_password, UserMixin, RoleMixin

from application.database import db
from validations.RoleValidations import RoleValidations


class Model(db.Model):
    __abstract__ = True

    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    updated_on = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdStatus(Enum):
    PENDING = 'Pending'
    ACCEPTED = 'Accepted'
    REJECTED = 'Rejected'


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

    def to_dict(self, exclude=None):
        exclude = exclude or []
        data = {
            "userid": self.id,
            "username": self.username,
            "company_name": self.company_name,
            "industry_type": self.industry_type,
            "description": self.description,
            "status": self.status,
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
    status = db.Column(db.Enum(AdStatus), default=AdStatus.PENDING)
    visibility = db.Column(db.String, nullable=False, default='private')
    ads = db.relationship('Ads', backref='campaign', lazy=True)


class Ads(Model):
    __tablename__ = 'ads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)
    status = db.Column(db.String, nullable=False, default='Pending')
    request = db.Column(db.String, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    requirement = db.Column(db.String, nullable=False)
    messages = db.Column(db.String)
