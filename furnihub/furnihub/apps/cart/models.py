from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Product
from decimal import Decimal

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Cart (Session: {self.session_id})"
    
    def get_total_items(self):
        """Get total number of items in cart"""
        return sum(item.quantity for item in self.items.all())
    
    def get_subtotal(self):
        """Get subtotal of all items in cart"""
        return sum(item.get_total_price() for item in self.items.all())
    
    def get_tax(self):
        """Calculate tax (10% by default) - Fixed Decimal multiplication"""
        subtotal = self.get_subtotal()
        # Convert 0.1 to Decimal to avoid type mixing
        tax_rate = Decimal('0.1')  # 10% tax
        return subtotal * tax_rate
    
    def get_total(self):
        """Get total including tax"""
        return self.get_subtotal() + self.get_tax()
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def get_total_price(self):
        """Get total price for this cart item"""
        # Convert to Decimal for consistent math
        price = self.product.price
        quantity = Decimal(str(self.quantity))
        return price * quantity