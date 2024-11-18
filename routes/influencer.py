from flask_jwt_extended import jwt_required, get_jwt
from flask_restful import Resource, reqparse, abort
from sqlalchemy.exc import IntegrityError

from application import db
from application.models import SocialMediaProfile, Influencer, User, Role
from application.response import success, internal_server_error, resource_not_found
from application.tasks import update_follower_counts


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
    def post(self):
        args = self.influencer_input_fields.parse_args()
        about = args["about"]
        category = args["category"]
        social_media_profiles = args["social_media_profiles"]

        current_user = get_jwt()
        user_id = current_user["user_id"]
        username = current_user["username"]

        # Extract and validate social media usernames
        usernames = [profile["username"] for profile in social_media_profiles]
        existing_usernames = [
            username[0] for username in db.session.query(SocialMediaProfile.username)
            .filter(SocialMediaProfile.username.in_(usernames))
            .all()
        ]
        if existing_usernames:
            abort(400, message=f"Usernames {', '.join(existing_usernames)} are already in use.")

        # Assign influencer role if not already assigned
        influencer_role = Role.query.filter_by(name="influencer").one_or_none()
        if not influencer_role:
            abort(500, message="Influencer role not found.")

        user = User.query.filter_by(id=user_id).one_or_none()
        if not user:
            return resource_not_found("User not found.")

        if influencer_role not in user.roles:
            user.roles.append(influencer_role)

        # Create Influencer
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

            # Add social media profiles
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
            abort(400, message="Integrity error occurred. Please check your inputs.")
        except Exception as e:
            db.session.rollback()
            abort(500, message=f"An error occurred while creating the influencer: {e}")
