from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
import paypalrestsdk
import stripe
from .models import Payment, PaymentLog
from apps.orders.models import Order
from .serializers import PaymentSerializer
import json
# import paypalrestsdk
# import stripe

# Configure PayPal
# paypalrestsdk.configure({
#     "mode": settings.PAYPAL_MODE,
#     "client_id": settings.PAYPAL_CLIENT_ID,
#     "client_secret": settings.PAYPAL_CLIENT_SECRET
# })

# Configure Stripe if needed
# stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, 'STRIPE_SECRET_KEY') else None

@login_required
def payment_view(request, order_id):
    """Payment page for an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.payment_status == 'paid':
        messages.warning(request, 'This order has already been paid')
        return redirect('orders:order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'paypal_client_id': settings.PAYPAL_CLIENT_ID,
        'stripe_publishable_key': settings.STRIPE_PUBLISHABLE_KEY if hasattr(settings, 'STRIPE_PUBLISHABLE_KEY') else None,
    }
    return render(request, 'payments/payment.html', context)

@login_required
@require_POST
def process_paypal_payment(request, order_id):
    """Process PayPal payment"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Create payment record
    payment = Payment.objects.create(
        user=request.user,
        order=order,
        payment_method='paypal',
        amount=order.total,
        payment_status='processing',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Create PayPal payment
    paypal_payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": request.build_absolute_uri(f'/payments/paypal/execute/{order.id}/'),
            "cancel_url": request.build_absolute_uri(f'/payments/paypal/cancel/{order.id}/')
        },
        "transactions": [{
            "amount": {
                "total": str(order.total),
                "currency": "USD"
            },
            "description": f"Order #{order.order_number}"
        }]
    })
    
    if paypal_payment.create():
        payment.gateway_reference = paypal_payment.id
        payment.gateway_response = {
            'paypal_payment_id': paypal_payment.id,
            'state': paypal_payment.state
        }
        payment.save()
        
        # Find approval URL
        for link in paypal_payment.links:
            if link.rel == "approval_url":
                return redirect(link.href)
    
    # If creation failed
    payment.payment_status = 'failed'
    payment.save()
    
    PaymentLog.objects.create(
        payment=payment,
        event_type='creation_failed',
        message='Failed to create PayPal payment',
        data={'error': str(paypal_payment.error) if hasattr(paypal_payment, 'error') else 'Unknown error'}
    )
    
    messages.error(request, 'Payment processing failed. Please try again.')
    return redirect('payments:payment_view', order_id=order.id)

@login_required
def execute_paypal_payment(request, order_id):
    """Execute PayPal payment after approval"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment = get_object_or_404(Payment, order=order, payment_method='paypal')
    
    payment_id = request.GET.get('paymentId')
    payer_id = request.GET.get('PayerID')
    
    if not payment_id or not payer_id:
        messages.error(request, 'Invalid payment request')
        return redirect('payments:payment_view', order_id=order.id)
    
    paypal_payment = paypalrestsdk.Payment.find(payment_id)
    
    if paypal_payment.execute({"payer_id": payer_id}):
        # Payment successful
        payment.payment_status = 'completed'
        payment.gateway_response = {
            'paypal_payment_id': payment_id,
            'payer_id': payer_id,
            'state': paypal_payment.state
        }
        payment.save()
        
        # Mark order as paid
        order.payment_status = 'paid'
        order.save()
        
        PaymentLog.objects.create(
            payment=payment,
            event_type='payment_completed',
            message='PayPal payment completed successfully',
            data={'paypal_payment_id': payment_id}
        )
        
        messages.success(request, 'Payment completed successfully!')
        return redirect('orders:order_confirmation', order_id=order.id)
    else:
        # Payment failed
        payment.payment_status = 'failed'
        payment.save()
        
        PaymentLog.objects.create(
            payment=payment,
            event_type='payment_failed',
            message='PayPal payment execution failed',
            data={'error': str(paypal_payment.error) if hasattr(paypal_payment, 'error') else 'Unknown error'}
        )
        
        messages.error(request, 'Payment failed. Please try again.')
        return redirect('payments:payment_view', order_id=order.id)

@login_required
def cancel_paypal_payment(request, order_id):
    """Handle PayPal payment cancellation"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment = get_object_or_404(Payment, order=order, payment_method='paypal')
    
    payment.payment_status = 'cancelled'
    payment.save()
    
    PaymentLog.objects.create(
        payment=payment,
        event_type='payment_cancelled',
        message='PayPal payment cancelled by user'
    )
    
    messages.info(request, 'Payment was cancelled.')
    return redirect('payments:payment_view', order_id=order.id)

@login_required
@require_POST
def process_stripe_payment(request, order_id):
    """Process Stripe payment"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    try:
        # Create payment record
        payment = Payment.objects.create(
            user=request.user,
            order=order,
            payment_method='stripe',
            amount=order.total,
            payment_status='processing',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Get token from request
        token = request.POST.get('stripeToken')
        
        # Create charge on Stripe
        charge = stripe.Charge.create(
            amount=int(order.total * 100),  # Stripe expects cents
            currency="usd",
            source=token,
            description=f"Order #{order.order_number}"
        )
        
        if charge.paid:
            # Payment successful
            payment.payment_status = 'completed'
            payment.gateway_reference = charge.id
            payment.gateway_response = charge
            payment.save()
            
            # Mark order as paid
            order.payment_status = 'paid'
            order.save()
            
            PaymentLog.objects.create(
                payment=payment,
                event_type='payment_completed',
                message='Stripe payment completed successfully',
                data={'charge_id': charge.id}
            )
            
            messages.success(request, 'Payment completed successfully!')
            return redirect('orders:order_confirmation', order_id=order.id)
        else:
            raise Exception('Payment failed')
            
    except Exception as e:
        if payment:
            payment.payment_status = 'failed'
            payment.save()
            
            PaymentLog.objects.create(
                payment=payment,
                event_type='payment_failed',
                message='Stripe payment failed',
                data={'error': str(e)}
            )
        
        messages.error(request, f'Payment failed: {str(e)}')
        return redirect('payments:payment_view', order_id=order.id)

@login_required
def payment_success(request, order_id):
    """Generic payment success page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'payments/success.html', {'order': order})

@login_required
def payment_failed(request, order_id):
    """Generic payment failed page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'payments/failed.html', {'order': order})

# Webhook handlers for payment gateways
@csrf_exempt
def paypal_webhook(request):
    """Handle PayPal webhooks"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            event_type = data.get('event_type')
            
            # Find payment by gateway reference
            resource = data.get('resource', {})
            payment_id = resource.get('id')
            
            if payment_id:
                payment = Payment.objects.filter(gateway_reference=payment_id).first()
                if payment:
                    PaymentLog.objects.create(
                        payment=payment,
                        event_type=f'webhook_{event_type}',
                        message='PayPal webhook received',
                        data=data
                    )
                    
                    if event_type == 'PAYMENT.SALE.COMPLETED':
                        payment.payment_status = 'completed'
                        payment.save()
                        payment.order.payment_status = 'paid'
                        payment.order.save()
                    
                    return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'ok'})

@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks"""
    if request.method == 'POST':
        try:
            payload = request.body
            sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            # Handle the event
            if event['type'] == 'charge.succeeded':
                charge = event['data']['object']
                payment = Payment.objects.filter(gateway_reference=charge['id']).first()
                
                if payment:
                    payment.payment_status = 'completed'
                    payment.save()
                    payment.order.payment_status = 'paid'
                    payment.order.save()
                    
                    PaymentLog.objects.create(
                        payment=payment,
                        event_type='webhook_charge_succeeded',
                        message='Stripe charge succeeded webhook received',
                        data=charge
                    )
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
    return JsonResponse({'status': 'ok'})

# API Views
class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        payment = self.get_object()
        logs = payment.logs.all()
        data = [
            {
                'event_type': log.event_type,
                'message': log.message,
                'created_at': log.created_at
            }
            for log in logs
        ]
        return Response(data)

# Create your views here.
