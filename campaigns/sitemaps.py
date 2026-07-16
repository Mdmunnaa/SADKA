from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Campaign


class CampaignSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return Campaign.objects.exclude(status='paused')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('campaign_detail', args=[obj.slug])


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return ['home', 'campaign_list', 'blog_list']

    def location(self, item):
        return reverse(item)
