from flask import request
from flask_jwt_extended import jwt_required, get_jwt
from flask_restful import Resource, reqparse, abort
from sqlalchemy.exc import IntegrityError

from application import db
from application.models import SocialMediaProfile, Influencer, User, Role
from application.response import success, internal_server_error, resource_not_found
from services.tasks import update_follower_counts
from routes.decorators import jwt_roles_required


class InfluencerAPI(Resource):
    def __init__(self):
        self.influencer_input_fields = reqparse.RequestParser()
        self.influencer_input_fields.add_argument("about", type=str, required=True, help="About section is required.")
        self.influencer_input_fields.add_argument("category", type=str, required=True, help="Category is required.")
        self.influencer_input_fields.add_argument(
            "social_media_profiles",
            type=dict,
            action="append",
            required=True,
            help="List of social media profiles is required."
        )

    @jwt_required()
    def get(self, influencer_id=None):
        return self.__get_influencer_details(influencer_id)

    @jwt_required()
    def post(self):
        return self.__influencer_registration()

    @jwt_required()
    @jwt_roles_required('influencer')
    def patch(self):
        return self.__update_influencer_profile()

    def __influencer_registration(self):
        args = self.influencer_input_fields.parse_args()
        about = args["about"]
        category = args["category"]
        social_media_profiles = args["social_media_profiles"]

        current_user = get_jwt()
        user_id = current_user["user_id"]
        username = current_user["username"]

        usernames = [profile["username"] for profile in social_media_profiles]
        existing_usernames = [
            username[0].lower() for username in db.session.query(SocialMediaProfile.username)
            .filter(db.func.lower(SocialMediaProfile.username).in_([u.lower() for u in usernames]))
            .all()
        ]
        if existing_usernames:
            abort(400, message=f"Usernames {', '.join(existing_usernames)} are already in use.")

        influencer_role = Role.query.filter_by(name="influencer").one_or_none()
        if not influencer_role:
            abort(500, message="Influencer role not found.")

        user = User.query.filter_by(id=user_id).one_or_none()
        if not user:
            return resource_not_found("User not found.")

        if influencer_role not in user.roles:
            user.roles.append(influencer_role)

        influencer = Influencer(
            userid=user_id,
            username=username,
            about=about,
            followers=0,
            category=category
        )
        try:
            db.session.add(influencer)
            db.session.commit()

            for profile in social_media_profiles:
                if "platform" not in profile or "username" not in profile:
                    abort(400, message="Each social media profile must include 'platform' and 'username'.")
                social_media_profile = SocialMediaProfile(
                    platform=profile["platform"],
                    username=profile["username"],
                    followers=0,
                    influencer_id=influencer.id
                )
                db.session.add(social_media_profile)

            db.session.commit()

            update_follower_counts.delay(influencer.id)

            return success(influencer.to_dict())

        except IntegrityError as e:
            db.session.rollback()
            abort(400, message=f"Integrity error occurred. Please check your inputs : {e}")
        except Exception as e:
            db.session.rollback()
            abort(500, message=f"An error occurred while creating the influencer: {e}")

    def __get_influencer_details(self, influencer_id):
        if influencer_id is None:
            endpoint = request.endpoint
            if endpoint == 'routes.influencer_meta':
                return self.__get_influencer_meta()
            elif endpoint == 'routes.influencer_profile_list':
                return self.__get_influencer_list()

        influencer = Influencer.query.filter_by(id=influencer_id).first()
        if not influencer:
            return resource_not_found("Influencer not found")

        user = User.query.get(influencer.userid)
        ads = [{"id": ad.id,
                "requirement": ad.requirement,
                "amount": ad.amount,
                "status": ad.status.value,
                "campaign_name": ad.campaign.name
                }
               for ad in influencer.ads  if ad.deleted_on is None]
        return success({
            "username": influencer.username,
            "about": influencer.about,
            "category": influencer.category,
            "followers": influencer.followers,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "ads": ads,
            }
        )

    def __get_influencer_meta(self):
        current_user = get_jwt()
        influencer = Influencer.query.filter_by(userid=current_user['user_id']).one()
        influencer_data = influencer.to_dict()
        return success(influencer_data)

    def __get_influencer_list(self):
        influencers = Influencer.query.all()
        influencer_list = [influencer.to_dict() for influencer in influencers]
        return success(influencer_list)


    def __update_influencer_profile(self):
        args = self.influencer_input_fields.parse_args()
        about = args.get("about")
        category = args.get("category")
        social_media_profiles = args.get("social_media_profiles")

        current_user = get_jwt()
        influencer = Influencer.query.filter_by(userid=current_user["user_id"]).one_or_none()

        if not influencer:
            return resource_not_found("Influencer not found.")

        try:
            if about:
                influencer.about = about
            if category:
                influencer.category = category

            if social_media_profiles:
                SocialMediaProfile.query.filter_by(influencer_id=influencer.id).delete()
                for profile in social_media_profiles:
                    if "platform" not in profile or "username" not in profile:
                        abort(400, message="Each social media profile must include 'platform' and 'username'.")
                    social_media_profile = SocialMediaProfile(
                        platform=profile["platform"],
                        username=profile["username"],
                        followers=0,
                        influencer_id=influencer.id
                    )
                    db.session.add(social_media_profile)

            db.session.commit()
            return success(influencer.to_dict())

        except IntegrityError as e:
            db.session.rollback()
            abort(400, message=f"Integrity error occurred. Please check your inputs: {e}")
        except Exception as e:
            db.session.rollback()
            return internal_server_error(f"An error occurred: {e}")

