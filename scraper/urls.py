from django.urls import path, include
from . import views

urlpatterns = [

    path('', views.index, name='scraper'),
    path('count/', views.row_ajax, name='count'),
    path('stop/', views.stop_scrap, name='stop_scrap'),
    path('show/', views.show, name='show'),
    path('radius/', views.radius_check, name='radius'),
    path('faq/', views.faq, name='faq'),
]
