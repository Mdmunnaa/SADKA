from django.urls import path
from . import views
from . import zakat_views

urlpatterns = [
    path('donate/<slug:slug>/', views.donate, name='donate'),
    path('donation/success/<int:pk>/', views.donation_success, name='donation_success'),
    path('recurring-sadaqah/', views.recurring_signup, name='recurring_signup'),
    path('zakat-calculator/', zakat_views.zakat_calculator, name='zakat_calculator'),
]
