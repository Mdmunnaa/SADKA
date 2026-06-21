from django.urls import path, register_converter
from . import views
from .converters import UnicodeSlugConverter

try:
    register_converter(UnicodeSlugConverter, 'uslug')
except ValueError:
    pass  # Already registered

urlpatterns = [
    path('', views.home, name='home'),
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy, name='privacy'),
    path('faq/', views.faq, name='faq'),
    path('volunteer/', views.volunteer_signup, name='volunteer_signup'),
    path('campaigns/<uslug:slug>/', views.campaign_detail, name='campaign_detail'),
]
