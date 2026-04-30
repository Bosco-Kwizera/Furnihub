from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.products.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('cart/', include('apps.cart.urls')),
    path('orders/', include('apps.orders.urls')),
    path('payments/', include('apps.payments.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('admin-dashboard/', include('apps.admin_dashboard.urls')),
    path('newsletter/', include('apps.newsletter.urls')),
    
    # ========== STATIC PAGES FOR FOOTER ==========
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('contact/', TemplateView.as_view(template_name='pages/contact.html'), name='contact'),
    path('blog/', TemplateView.as_view(template_name='pages/blog.html'), name='blog'),
    path('showrooms/', TemplateView.as_view(template_name='pages/showrooms.html'), name='showrooms'),
    path('gift-cards/', TemplateView.as_view(template_name='pages/gift-cards.html'), name='gift_cards'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)