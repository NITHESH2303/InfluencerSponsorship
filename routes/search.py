from flask_restful import Resource, request

from application.models import Influencer, Campaign

class SearchAPI(Resource):

  def get(self):
    print(request.args)
    if "influencer" in request.url:
      if 'niche' in request.args:
        influencers = Influencer.query.filter(Influencer.category.like('%'+request.args['niche']+'%')).all()
        return influencers
      if 'username' in request.args:
        influencers = Influencer.query.filter(Influencer.username.like('%'+request.args['username']+'%')).all()
        return influencers
      if 'rating' in request.orgs:
        influencers = Influencer.query.filter(Influencer.followers.equals(int(request.args['rating']))).all()
        return influencers
      return None
    else:
      if 'niche' in request.args:
        campaigns = Campaign.query.filter(Campaign.niche.like('%'+request.args['niche']+'%')).all()
        return campaigns
      if 'description' in request.args:
        campaigns = Campaign.query.filter(Campaign.description.like('%'+request.args['description']+'%')).all()
        return campaigns
      return None