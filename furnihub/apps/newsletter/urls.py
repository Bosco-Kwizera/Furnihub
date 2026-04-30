from django.urls import path
from . import views

app_name = 'newsletter'

urlpatterns = [
    path('subscribe/', views.subscribe, name='subscribe'),
    path('unsubscribe/', views.unsubscribe, name='unsubscribe'),
    path('admin/campaigns/', views.campaign_list, name='campaign_list'),
    path('admin/campaigns/create/', views.create_campaign, name='create_campaign'),
]