from django.urls import path
from . import views

urlpatterns = [
    path('register/',            views.donor_register,     name='donor_register'),
    path('login/',               views.donor_login,        name='donor_login'),
    path('logout/',              views.donor_logout,       name='donor_logout'),
    path('dashboard/',           views.donor_dashboard,    name='donor_dashboard'),
    path('profile/edit/',        views.donor_profile_edit, name='donor_profile_edit'),
    path('receipt/<int:pk>/',    views.donation_receipt,   name='donation_receipt'),
]
