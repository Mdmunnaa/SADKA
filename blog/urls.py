from django.urls import path, register_converter
from . import views
from campaigns.converters import UnicodeSlugConverter

try:
    register_converter(UnicodeSlugConverter, 'uslug')
except ValueError:
    pass  # Already registered (e.g. by campaigns.urls)

urlpatterns = [
    path('blog/', views.blog_list, name='blog_list'),
    path('blog/<uslug:slug>/', views.blog_detail, name='blog_detail'),
]
