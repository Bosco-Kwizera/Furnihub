from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('track/<int:order_id>/', views.order_tracking, name='order_tracking'),
    path('cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
]