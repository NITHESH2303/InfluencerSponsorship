from flask_restful import Resource
from application.models import User, Campaign, Sponsor, Influencer
from application.response import success

class AdminAPI(Resource):
    @staticmethod
    def get_overview_stats():
        users_count = User.query.count()
        campaigns_count = Campaign.query.count()
        flagged_sponsors = Sponsor.query.filter(Sponsor.is_flagged == True).count()
        flagged_influencers = Influencer.query.filter(Influencer.is_flagged == True).count()

        return success({
            "total_users": users_count,
            "total_campaigns": campaigns_count,
            "flagged_sponsors": flagged_sponsors,
            "flagged_influencers": flagged_influencers
        })

    def get(self):
        return self.get_overview_stats()
