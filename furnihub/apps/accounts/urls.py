from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Password Reset URLs - Using the correct namespace
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='/accounts/password-reset/done/'  # Explicit URL instead of reverse
         ),
         name='password_reset'),
    
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='/accounts/reset/done/'
         ),
         name='password_reset_confirm'),
    
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
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