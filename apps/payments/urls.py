from django.urls import path
from . import views

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('<int:order_id>/', views.payment_view, name='payment_view'),
    
    # PayPal
    path('paypal/process/<int:order_id>/', views.process_paypal_payment, name='process_paypal'),
    path('paypal/execute/<int:order_id>/', views.execute_paypal_payment, name='execute_paypal'),
    path('paypal/cancel/<int:order_id>/', views.cancel_paypal_payment, name='cancel_paypal'),
    
    # Stripe
    path('stripe/process/<int:order_id>/', views.process_stripe_payment, name='process_stripe'),
    
    # Webhooks
    path('webhook/paypal/', views.paypal_webhook, name='paypal_webhook'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    
    # Status pages
    path('success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('failed/<int:order_id>/', views.payment_failed, name='payment_failed'),
]