from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from campaigns.sitemaps import CampaignSitemap, StaticViewSitemap
from campaigns.dashboard_views import admin_dashboard

admin.site.site_header = "সহায় - Admin Panel"
admin.site.site_title = "সহায় Admin"
admin.site.index_title = "ড্যাশবোর্ড"

sitemaps = {
    'campaigns': CampaignSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots_txt'),
    path('', include('campaigns.urls')),
    path('', include('donations.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'campaigns.views.custom_404'
handler500 = 'campaigns.views.custom_500'
