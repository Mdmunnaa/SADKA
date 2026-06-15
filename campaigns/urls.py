from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/<slug:slug>/', views.campaign_detail, name='campaign_detail'),
]
