from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Order Management
    path('orders/', views.orders_list, name='orders_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/update/', views.update_order_status, name='update_order_status'),
    
    # Product Management
    path('products/', views.products_list, name='products_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:product_id>/delete/', views.delete_product, name='delete_product'),
    
    # Category Management
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/add/', views.add_category, name='add_category'),
    
    # User Management
    path('users/', views.users_list, name='users_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),
    path('users/<int:user_id>/make-staff/', views.make_staff, name='make_staff'),
    path('users/<int:user_id>/make-superuser/', views.make_superuser, name='make_superuser'),
    path('users/<int:user_id>/remove-staff/', views.remove_staff, name='remove_staff'),
    
    # User Roles & Permissions
    path('user-roles/', views.user_roles, name='user_roles'),
    path('api/group-permissions/<int:group_id>/', views.get_group_permissions, name='get_group_permissions'),
    # Add to your urlpatterns
    path('reports/', views.reports_view, name='reports'),
    path('export/orders/csv/', views.export_orders_csv, name='export_orders_csv'),
    path('export/orders/excel/', views.export_orders_excel, name='export_orders_excel'),
    path('export/products/csv/', views.export_products_csv, name='export_products_csv'),
    path('orders/<int:order_id>/update-payment/', views.update_payment_status, name='update_payment_status'),
]