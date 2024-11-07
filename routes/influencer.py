from flask_jwt_extended import jwt_required, get_jwt
from flask_restful import Resource, reqparse, abort

from application import db
from application.models import SocialMediaProfile, Influencer
from application.response import success
from application.tasks import update_follower_counts

class InfluencerAPI(Resource):
    def __init__(self):
        self.influencer_input_fields = reqparse.RequestParser()
        self.influencer_input_fields.add_argument("about", type=str)
        self.influencer_input_fields.add_argument("category", type=str)
        self.influencer_input_fields.add_argument("social_media_profiles",
                                                  type=dict,
                                                  action="append",
                                                  required=True,
                                                  help="List of social media profiles is required")

    @jwt_required()
    def post(self):
        args = self.influencer_input_fields.parse_args()
        about = args['about']
        category = args['category']
        social_media_profiles = args['social_media_profiles']

        current_user = get_jwt()

        userid =current_user['user_id']
        username = current_user['username']
        usernames = [profile['username'] for profile in social_media_profiles]
        existing_usernames = (
            db.session.query(SocialMediaProfile.username)
            .filter(SocialMediaProfile.username.in_(usernames))
            .all()
        )

        if existing_usernames:
            abort(400, message=f"Usernames {', '.join(existing_usernames)} are already in use.")

        influencer = Influencer(
            userid=userid,
            username=username,
            about=about,
            followers=0,
            category=category
        )

        try:
            db.session.add(influencer)
            db.session.commit()

            for profile in social_media_profiles:
                social_media_profile = SocialMediaProfile(
                    platform=profile['platform'],
                    username=profile['username'],
                    followers=0,
                    influencer_id=influencer.id
                )
                db.session.add(social_media_profile)

            db.session.commit()

            update_follower_counts.delay(influencer.id)

            return success("Influencer created successfully")

        except Exception as e:
            db.session.rollback()
            abort(500, message=f"An error {e} occurred while creating the influencer.")


    # def get_twitter_follower_count(self, username):
    #     url = f'https://api.twitter.com/2/users/by/username/{username}?user.fields=public_metrics"'
    #     headers = {'Authorization': f'Bearer {Tokens.get_twitter_bearer_token()}'}
    #     response = requests.get(url, headers=headers)
    #
    #     if response.status_code == 200:
    #         data = response.json()
    #         followers_count = data['data']['public_metrics']['followers_count']
    #         return success({"followers": followers_count})
    #     else:
    #         return create_response({"error": "Failed to retrieve data from Twitter"}, response.status_code)