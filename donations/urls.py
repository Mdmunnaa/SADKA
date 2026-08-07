from django.urls import path
from . import views
from . import zakat_views

urlpatterns = [
    path('donate/<uslug:slug>/', views.donate, name='donate'),
    path('donation/success/<int:pk>/', views.donation_success, name='donation_success'),
    path('donation/<int:pk>/share-card.png', views.donation_share_card, name='donation_share_card'),
    path('recurring-sadaqah/', views.recurring_signup, name='recurring_signup'),
    path('zakat-calculator/', zakat_views.zakat_calculator, name='zakat_calculator'),
    path('payments/success/<str:gateway_name>/', views.payment_success, name='payment_success'),
    path('payments/fail/<str:gateway_name>/', views.payment_fail, name='payment_fail'),
    path('payments/cancel/<str:gateway_name>/', views.payment_cancel, name='payment_cancel'),
    path('payments/ipn/<str:gateway_name>/', views.payment_ipn, name='payment_ipn'),
]
