from django.db import models
from django.contrib.auth.models import User
from apps.orders.models import Order
import uuid

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=100, unique=True, editable=False)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Amount details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Payment gateway details
    gateway_reference = models.CharField(max_length=255, blank=True)
    gateway_response = models.JSONField(null=True, blank=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            self.transaction_id = f"PAY-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)
    
    def mark_as_completed(self):
        self.payment_status = 'completed'
        self.completed_at = models.DateTimeField(auto_now=True)
        self.save()
        
        # Update order payment status
        self.order.payment_status = 'paid'
        self.order.save()

class PaymentLog(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='logs')
    event_type = models.CharField(max_length=50)
    message = models.TextField()
    data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment.transaction_id} - {self.event_type} at {self.created_at}"

# Create your models here.
