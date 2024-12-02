from flask import request
from flask_restful import Resource
from sqlalchemy import func

from application.models import User, Sponsor, Influencer, Campaign, Ads, Role
from application.response import success, internal_server_error

class SearchAPI(Resource):
    def get(self):
        search_type = request.args.get('type', 'user')
        keyword = request.args.get('keyword', '')
        role = request.args.get('role', None)
        min_followers = request.args.get('min_followers', None, type=int)
        ad_request_count = request.args.get('ad_request_count', None, type=int)
        campaign_count = request.args.get('campaign_count', None, type=int)
        spent_amount = request.args.get('spent_amount', None, type=float)
        ads_count = request.args.get('ads_count', None, type=int)
        campaign_budget = request.args.get('campaign_budget', None, type=float)

        try:
            if search_type == 'user':
                query = User.query.join(User.roles)
                if keyword:
                    query = query.filter(User.username.ilike(f'%{keyword}%') | User.email.ilike(f'%{keyword}%'))
                if role:
                    query = query.filter(Role.name == role)

                if role == 'Influencer':
                    query = query.join(Influencer)
                    if min_followers:
                        query = query.filter(Influencer.followers >= min_followers)
                    if ad_request_count:
                        query = query.outerjoin(Ads).group_by(Influencer.id).having(func.count(Ads.id) >= ad_request_count)

                elif role == 'Sponsor':
                    query = query.join(Sponsor)
                    if campaign_count:
                        query = query.outerjoin(Campaign).group_by(Sponsor.id).having(func.count(Campaign.id) >= campaign_count)

                users = query.all()
                results = [user.to_dict() for user in users]

            elif search_type == 'campaign':
                query = Campaign.query
                if keyword:
                    query = query.filter(Campaign.name.ilike(f'%{keyword}%') | Campaign.description.ilike(f'%{keyword}%'))
                if campaign_budget:
                    query = query.filter(Campaign.budget >= campaign_budget)
                if ads_count:
                    query = query.outerjoin(Ads).group_by(Campaign.id).having(func.count(Ads.id) >= ads_count)
                if spent_amount:
                    query = query.outerjoin(Ads).group_by(Campaign.id).having(func.sum(Ads.amount) >= spent_amount)

                campaigns = query.all()
                results = [campaign.to_dict() for campaign in campaigns]

            else:
                return internal_server_error("Invalid search type")

            return success(results)

        except Exception as e:
            return internal_server_error(str(e))
