from django.contrib import admin
from django.urls import path, include, register_converter
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from campaigns.sitemaps import CampaignSitemap, StaticViewSitemap
from blog.sitemaps import BlogSitemap
from campaigns.dashboard_views import admin_dashboard
from campaigns.converters import UnicodeSlugConverter

# Register the Unicode-aware slug converter once, before any app urls (which use it) are included.
register_converter(UnicodeSlugConverter, 'uslug')

admin.site.site_header = "সহায় - Admin Panel"
admin.site.site_title = "সহায় Admin"
admin.site.index_title = "ড্যাশবোর্ড"

sitemaps = {
    'campaigns': CampaignSitemap,
    'blog': BlogSitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots_txt'),
    path('accounts/', include('accounts.urls')),
    path('', include('campaigns.urls')),
    path('', include('donations.urls')),
    path('', include('blog.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'campaigns.views.custom_404'
handler500 = 'campaigns.views.custom_500'
