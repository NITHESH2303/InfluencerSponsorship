from flask_restful import Resource
from sqlalchemy import func
from application import db
from application.models import User, Campaign, Ads, Influencer
from application.response import success
from sklearn.cluster import KMeans
import numpy as np

class StatisticsAPI(Resource):

    def get(self):
        results = {}
        results["statistics"] = self.get_statistics()
        # results["influencer_analytics"] = self.get_influencer_analytics()
        results["time_trends"] = self.get_time_trends()
        results["influencer_clusters"] = self.get_influencer_clusters()
        return success(results)

    def get_statistics(self):
        total_users = db.session.query(func.count(User.id)).scalar()
        total_campaigns = db.session.query(func.count(Campaign.id)).scalar()
        public_campaigns = db.session.query(func.count(Campaign.id)).filter(Campaign.visibility == "public").scalar()
        private_campaigns = total_campaigns - public_campaigns
        total_ad_requests = db.session.query(func.count(Ads.id)).scalar()

        active_users = db.session.query(func.count(User.id)).filter(User.last_login >= func.date('now', '-7 days')).scalar()

        campaigns_by_date = db.session.query(
            func.strftime("%Y-%m-%d", Campaign.created_on), func.count(Campaign.id)
        ).group_by(func.strftime("%Y-%m-%d", Campaign.created_on)).all()

        ad_requests_by_date = db.session.query(
            func.strftime("%Y-%m-%d", Ads.created_on), func.count(Ads.id)
        ).group_by(func.strftime("%Y-%m-%d", Ads.created_on)).all()

        total_budget = db.session.query(func.sum(Campaign.budget)).scalar() or 0
        avg_budget = db.session.query(func.avg(Campaign.budget)).scalar() or 0

        campaigns_by_date = {date: count for date, count in campaigns_by_date}
        ad_requests_by_date = {date: count for date, count in ad_requests_by_date}

        data = {
            "overview": {
                "total_users": total_users,
                "active_users": active_users,
            },
            "campaigns": {
                "total": total_campaigns,
                "public": public_campaigns,
                "private": private_campaigns,
                "by_date": campaigns_by_date,
            },
            "ad_requests": {
                "total": total_ad_requests,
                "by_date": ad_requests_by_date,
            },
            "monetary": {
                "total_budget": total_budget,
                "avg_budget": avg_budget,
            },
        }

        return data

    # def get_influencer_analytics(self):
    #     reach_distribution = db.session.query(
    #             func.case(
    #                 [
    #                     (Influencer.followers <= 1000, "Small"),
    #                     (Influencer.followers.between(1001, 10000), "Medium"),
    #                     (Influencer.followers > 10000, "Large")
    #                 ],
    #                 else_="Unknown"  # Optional: handle cases that don't match
    #             ).label("reach_category"),
    #             func.count(Influencer.id)
    #         ).group_by("reach_category").all()
    #
    #     top_categories = db.session.query(
    #         Influencer.category,
    #         func.count(Ads.id).label("ad_count")
    #     ).join(Ads, Ads.influencer_id == Influencer.id) \
    #         .filter(Ads.deleted_on.is_(None)) \
    #         .group_by(Influencer.category) \
    #         .order_by(func.count(Ads.id).desc()) \
    #         .limit(5).all()
    #
    #     # Convert query results to serializable format
    #     reach_distribution_dict = {category: count for category, count in reach_distribution}
    #     top_categories_dict = {category: ad_count for category, ad_count in top_categories}
    #
    #     data = {
    #         "reach_distribution": reach_distribution_dict,
    #         "top_categories": top_categories_dict
    #     }
    #
    #     return data

    def get_time_trends(self):
        campaigns_trend = db.session.query(
            func.strftime("%Y-%m-%d", Campaign.created_on), func.count(Campaign.id)
        ).filter(Campaign.created_on >= func.date('now', '-30 days')).group_by(func.strftime("%Y-%m-%d", Campaign.created_on)).all()

        ad_requests_trend = db.session.query(
            func.strftime("%Y-%m-%d", Ads.created_on), func.count(Ads.id)
        ).filter(Ads.created_on >= func.date('now', '-30 days')).group_by(func.strftime("%Y-%m-%d", Ads.created_on)).all()

        campaigns_trend_dict = {date: count for date, count in campaigns_trend}
        ad_requests_trend_dict = {date: count for date, count in ad_requests_trend}

        data = {
            "campaigns": campaigns_trend_dict,
            "ad_requests": ad_requests_trend_dict
        }

        return data

    def get_influencer_clusters(self):
        influencer_data = db.session.query(
            Influencer.id,
            Influencer.followers,
            func.count(Ads.id).label("ad_count")
        ).outerjoin(Ads, Ads.influencer_id == Influencer.id) \
            .filter(Ads.deleted_on.is_(None)) \
            .group_by(Influencer.id).all()

        data = np.array([[inf.followers, inf.ad_count] for inf in influencer_data])

        if len(data) < 3:
            return {"message": "Not enough data for clustering"}

        kmeans = KMeans(n_clusters=3, random_state=0).fit(data)

        clusters = [
            {"influencer_id": inf.id, "followers": inf.followers, "ad_count": inf.ad_count, "cluster": int(label)}
            for inf, label in zip(influencer_data, kmeans.labels_)
        ]

        return clusters