from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Product
import uuid


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('cash_on_delivery', 'Cash on Delivery'),
        ('mobile_money', 'Mobile Money'),
        ('paypal', 'PayPal'),
        ('stripe', 'Credit Card'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    MOBILE_MONEY_PROVIDERS = [
        ('mtn', 'MTN Mobile Money'),
        ('airtel', 'Airtel Money'),
        ('vodafone', 'Vodafone Cash'),
        ('orange', 'Orange Money'),
        ('tigo', 'Tigo Cash'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # Order details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash_on_delivery')
    
    # Mobile Money specific fields
    mobile_money_provider = models.CharField(max_length=20, choices=MOBILE_MONEY_PROVIDERS, blank=True, null=True)
    mobile_number = models.CharField(max_length=20, blank=True, null=True, help_text="Customer's mobile number for payment")
    
    # Totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Shipping information
    shipping_address = models.ForeignKey('accounts.Address', on_delete=models.PROTECT, related_name='orders')
    shipping_name = models.CharField(max_length=100)
    shipping_phone = models.CharField(max_length=15)
    
    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
    
    def __str__(self):
        return f"Order #{self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            self.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def get_items_count(self):
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items.all())
    
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'processing']
    
    def get_formatted_total(self):
        """Return formatted total"""
        return f"${self.total:.2f}"
    
    def get_payment_method_display(self):
        """Get human-readable payment method"""
        return dict(self.PAYMENT_METHOD_CHOICES).get(self.payment_method, self.payment_method)
    
    def get_mobile_money_provider_display(self):
        """Get human-readable mobile money provider"""
        if self.mobile_money_provider:
            return dict(self.MOBILE_MONEY_PROVIDERS).get(self.mobile_money_provider, self.mobile_money_provider)
        return None


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def save(self, *args, **kwargs):
        self.total = self.price * self.quantity
        super().save(*args, **kwargs)
    
    def get_item_total(self):
        """Get total for this line item"""
        return self.total


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Order Status History"
        verbose_name_plural = "Order Status Histories"
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_status_display()} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    def get_status_display(self):
        """Get human-readable status"""
        return dict(Order.STATUS_CHOICES).get(self.status, self.status)