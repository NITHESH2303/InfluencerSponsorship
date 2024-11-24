from flask_restful import Resource, request

from application.models import Influencer, Campaign

class SearchAPI(Resource):

  def get(self, pattern=''):
    if "influencer" in request.url:
      influencers = Influencer.query.filter(Influencer.category.like('%'+pattern+'%')).filter(Influencer.followers.like(pattern)).all()
      return influencers
    else:
      campaigns = Campaign.query.filter(Campaign.niche.like('%'+pattern+'%')).filter(Campaign.description.like('%'+pattern+'%')).all()
      return campaigns