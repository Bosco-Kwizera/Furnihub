from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = 'products'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('category/<slug:category_slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('product/<slug:category_slug>/<slug:product_slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('product/<int:product_id>/review/', views.add_review, name='add_review'),  # Make sure this line exists
    path('search/', views.ProductListView.as_view(), name='search'),
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='pages/contact.html'), name='contact'),
    path('blog/', TemplateView.as_view(template_name='pages/blog.html'), name='blog'),
    path('showrooms/', TemplateView.as_view(template_name='pages/showrooms.html'), name='showrooms'),
    path('gift-cards/', TemplateView.as_view(template_name='pages/gift-cards.html'), name='gift_cards'),
]