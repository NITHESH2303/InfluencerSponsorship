from application.response import success


class ReportsAPI:
    @staticmethod
    def generate_sponsor_monthly_report(sponsor, start_date, end_date):
        from application.models import Campaign, AdStatus

        # Query all campaigns for the sponsor within the date range
        campaigns = Campaign.query.filter(
            Campaign.sponsor_id == sponsor.id,
            # Campaign.deleted_on is None,
            # Campaign.start_date >= start_date,
            # Campaign.end_date <= end_date
        ).all()

        campaign_data = []
        total_ads = 0
        ads_by_status = {status.value: 0 for status in AdStatus}
        total_spent = 0
        total_budget = 0
        niches_targeted = set()
        # total_engagements = 0
        top_campaigns = []

        # Historical data placeholders
        historical_trends = {
            "spending_trends": [],
            "seasonality": {
                "months_with_high_engagement": [],
                "average_engagement_rate_by_month": {}
            }
        }

        # Processing each campaign
        for campaign in campaigns:
            campaign_ads = [ad for ad in campaign.ads if ad.deleted_on is None]
            spent_amount = sum(ad.amount for ad in campaign_ads)

            total_ads += len(campaign_ads)
            total_spent += spent_amount
            total_budget += campaign.budget

            for ad in campaign_ads:
                ads_by_status[ad.status.value] += 1

            niches_targeted.add(campaign.niche.value)

            # ROI calculation
            roi = (spent_amount / campaign.budget) if campaign.budget > 0 else 0
            top_campaigns.append({
                "campaign_name": campaign.name,
                "roi": roi,
                "spent": spent_amount,
                "budget": campaign.budget
            })

            # Campaign details
            campaign_data.append({
                "campaign_name": campaign.name,
                "status": campaign.status.value,
                "start_date": campaign.start_date,
                "end_date": campaign.end_date,
                "budget": campaign.budget,
                "spent_amount": spent_amount,
                "remaining_budget": campaign.budget - spent_amount,
            })

        # Sort top campaigns by ROI
        top_campaigns = sorted(top_campaigns, key=lambda x: x["roi"], reverse=True)[:5]

        # Generating historical trends
        historical_trends["spending_trends"] = [
            {"month": campaign.start_date.strftime("%B"), "amount_spent": sum(ad.amount for ad in campaign.ads)}
            for campaign in campaigns
        ]
        # Mocking engagement data
        historical_trends["seasonality"]["average_engagement_rate_by_month"] = {
            "January": 10, "June": 25
        }
        historical_trends["seasonality"]["months_with_high_engagement"] = ["June", "December"]

        # Audience segmentation insights
        audience_segmentation = {
            "top_performing_categories": list(niches_targeted),  # Assuming niches represent categories
            "engagement_by_region": {
                "North America": 60,
                "Europe": 25,
                "Asia": 15
            }
        }

        # Ad performance insights
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

        # Final report assembly
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
