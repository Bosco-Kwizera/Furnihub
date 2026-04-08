from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('category/<slug:category_slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('product/<slug:category_slug>/<slug:product_slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),  # Add this line
    path('search/', views.ProductListView.as_view(), name='search'),
]