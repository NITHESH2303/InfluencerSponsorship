from datetime import date

from flask import request
from flask_restful import Resource

from application.response import internal_server_error, success


class ReportsAPI(Resource):
    @staticmethod
    def generate_sponsor_monthly_report(sponsor, start_date=None, end_date=None):
        from application.models import Campaign, AdStatus

        if start_date is None and end_date is None:
            today = date.today()
            start_date = date(today.year, 1, 1)
            end_date = date(today.year, 12, 31)

            campaigns = Campaign.query.filter(
                Campaign.sponsor_id == sponsor.id,
                Campaign.deleted_on == None,
                Campaign.start_date >= start_date,
                Campaign.end_date <= end_date
            ).all()
        else:
            campaigns = Campaign.query.filter(
                Campaign.sponsor_id == sponsor.id,
            ).all()

        campaign_data = []
        total_ads = 0
        ads_by_status = {status.value: 0 for status in AdStatus}
        total_spent = 0
        total_budget = 0
        niches_targeted = set()
        top_campaigns = []


        historical_trends = {
            "spending_trends": [],
            "seasonality": {
                "months_with_high_engagement": [],
                "average_engagement_rate_by_month": {}
            }
        }


        for campaign in campaigns:
            campaign_ads = [ad for ad in campaign.ads if ad.deleted_on is None]
            spent_amount = sum(ad.amount for ad in campaign_ads)

            total_ads += len(campaign_ads)
            total_spent += spent_amount
            total_budget += campaign.budget

            for ad in campaign_ads:
                ads_by_status[ad.status.value] += 1

            niches_targeted.add(campaign.niche.value)


            roi = (spent_amount / campaign.budget) if campaign.budget > 0 else 0
            top_campaigns.append({
                "campaign_name": campaign.name,
                "roi": roi,
                "spent": spent_amount,
                "budget": campaign.budget,
                "campaign_status": campaign.status.value,
            })


            campaign_data.append({
                "campaign_name": campaign.name,
                "campaign_description": campaign.description,
                "status": campaign.status.value,
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "budget": campaign.budget,
                "spent_amount": spent_amount,
                "remaining_budget": campaign.budget - spent_amount,
            })


        top_campaigns = sorted(top_campaigns, key=lambda x: x["roi"], reverse=True)[:5]

        historical_trends["spending_trends"] = [
            {"month": campaign.start_date.strftime("%B"), "amount_spent": sum(ad.amount for ad in campaign.ads)}
            for campaign in campaigns
        ]

        historical_trends["seasonality"]["average_engagement_rate_by_month"] = {
            "January": 10, "June": 25
        }
        historical_trends["seasonality"]["months_with_high_engagement"] = ["June", "December"]


        audience_segmentation = {
            "top_performing_categories": list(niches_targeted),  # Assuming niches represent categories
            "engagement_by_region": {
                "North America": 60,
                "Europe": 25,
                "Asia": 15
            }
        }


        ad_performance_insights = {
            "cost_efficiency": {
                "average_cost_per_ad": total_spent / total_ads if total_ads > 0 else 0,
                # "cost_per_conversion": total_spent / total_engagements if total_engagements > 0 else 0
            }
        }

        # Conversion analysis
        # conversion_analysis = {
        #     "total_conversions": total_engagements,  # Assuming total engagements = total conversions
        #     "conversion_rate": (total_engagements / total_ads * 100) if total_ads > 0 else 0,
        #     "best_campaigns_by_conversion_rate": sorted(campaign_data, key=lambda x: x["engagements"], reverse=True)[:3]
        # }


        report = {
            "sponsor_name": sponsor.company_name,
            "report_period": {
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            },
            "total_ads": total_ads,
            "ads_by_status": ads_by_status,
            "total_spent": total_spent,
            "average_budget_utilization": (total_spent / total_budget * 100) if total_budget > 0 else 0,
            "top_campaigns": top_campaigns,
            "niches_targeted": list(niches_targeted),
            "campaign_data": campaign_data,
            "audience_segmentation": audience_segmentation,
            "ad_performance_insights": ad_performance_insights,
            # "conversion_analysis": conversion_analysis
        }

        return report

    def __export_campaigns(self, sponsor_id):
        from services.tasks import export_campaigns_as_csv
        if not sponsor_id:
            return internal_server_error('Sponsor ID is required')

        task = export_campaigns_as_csv.delay(sponsor_id)

        return success(f"Export initiated for task {task.id}! Check back later")

    def post(self, sponsor_id):
        endpoint = request.endpoint
        if endpoint == 'routes.export_campaigns':
            return self.__export_campaigns(sponsor_id)

    def get(self, sponsor_id):
        from application.models import Sponsor
        sponsor = Sponsor.query.get_or_404(sponsor_id)
        report = self.generate_sponsor_monthly_report(sponsor)
        return success(report)


