from django.urls import path
from . import views

urlpatterns = [
    path('donate/<slug:slug>/', views.donate, name='donate'),
    path('donation/success/<int:pk>/', views.donation_success, name='donation_success'),
]
