from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header = "সহায় - Admin Panel"
admin.site.site_title = "সহায় Admin"
admin.site.index_title = "ড্যাশবোর্ড"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('campaigns.urls')),
    path('', include('donations.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
