from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    
    # Addresses
    path('addresses/', views.addresses_view, name='addresses'),
    path('addresses/add/', views.add_address_view, name='add_address'),
    path('addresses/<int:address_id>/edit/', views.edit_address_view, name='edit_address'),
    path('addresses/<int:address_id>/delete/', views.delete_address_view, name='delete_address'),
    
    # Wishlist
    path('wishlist/', views.wishlist_view, name='wishlist'),
    
    # Orders
    path('orders/', views.orders_view, name='orders'),
]