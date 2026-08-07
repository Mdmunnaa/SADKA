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
    path('terms/', views.terms_of_service, name='terms'),
    path('faq/', views.faq, name='faq'),
    path('trustees/', views.trustees, name='trustees'),
    path('contact/', views.contact, name='contact'),
    path('transparency/', views.transparency, name='transparency'),
    path('volunteer/', views.volunteer_signup, name='volunteer_signup'),
    path('volunteer/dashboard/', views.volunteer_dashboard, name='volunteer_dashboard'),
    path('volunteer/id-card/download/', views.volunteer_id_card_download, name='volunteer_id_card_download'),
    path('volunteer/verify/<str:volunteer_id>/', views.volunteer_verify, name='volunteer_verify'),
    path('campaigns/<uslug:slug>/', views.campaign_detail, name='campaign_detail'),
]
