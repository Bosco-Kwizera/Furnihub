from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Product
from decimal import Decimal

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Cart'
        verbose_name_plural = 'Carts'

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Cart (Session: {self.session_id})"
    
    def get_total_items(self):
        """Get total number of items in cart"""
        total = sum(item.quantity for item in self.items.all())
        return total
    
    def get_subtotal(self):
        """Get subtotal of all items in cart"""
        subtotal = Decimal('0.00')
        for item in self.items.select_related('product').all():
            subtotal += item.get_total_price()
        return subtotal.quantize(Decimal('0.01'))
    
    def get_tax(self):
        """Calculate tax (10% by default)"""
        subtotal = self.get_subtotal()
        tax_rate = Decimal('0.10')  # 10% tax
        tax = (subtotal * tax_rate).quantize(Decimal('0.01'))
        return tax
    
    def get_total(self):
        """Get total including tax"""
        total = (self.get_subtotal() + self.get_tax()).quantize(Decimal('0.01'))
        return total
    
    def get_discount_total(self, discount_percentage=0):
        """Calculate total after discount"""
        if discount_percentage > 0:
            discount = (self.get_subtotal() * Decimal(str(discount_percentage)) / Decimal('100')).quantize(Decimal('0.01'))
            return (self.get_subtotal() - discount + self.get_tax()).quantize(Decimal('0.01'))
        return self.get_total()
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()
    
    def is_empty(self):
        """Check if cart is empty"""
        return self.get_total_items() == 0
    
    def get_cart_summary(self):
        """Get cart summary as dictionary"""
        return {
            'total_items': self.get_total_items(),
            'subtotal': float(self.get_subtotal()),
            'tax': float(self.get_tax()),
            'total': float(self.get_total()),
            'items': [
                {
                    'id': item.id,
                    'product_id': item.product.id,
                    'name': item.product.name,
                    'quantity': item.quantity,
                    'price': float(item.product.price),
                    'total': float(item.get_total_price()),
                    'image': item.product.images.first().image.url if item.product.images.exists() else None
                }
                for item in self.items.select_related('product').all()
            ]
        }


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product']
        ordering = ['-created_at']
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def get_total_price(self):
        """Get total price for this cart item"""
        price = self.product.price
        quantity = Decimal(str(self.quantity))
        total = (price * quantity).quantize(Decimal('0.01'))
        return total
    
    def increase_quantity(self, amount=1):
        """Increase quantity by given amount"""
        new_quantity = self.quantity + amount
        if new_quantity <= self.product.stock_quantity:
            self.quantity = new_quantity
            self.save()
            return True
        return False
    
    def decrease_quantity(self, amount=1):
        """Decrease quantity by given amount"""
        new_quantity = self.quantity - amount
        if new_quantity >= 1:
            self.quantity = new_quantity
            self.save()
            return True
        elif new_quantity <= 0:
            self.delete()
            return True
        return False
    
    def update_quantity(self, new_quantity):
        """Update quantity to specific value"""
        if new_quantity <= 0:
            self.delete()
            return True
        elif new_quantity <= self.product.stock_quantity:
            self.quantity = new_quantity
            self.save()
            return True
        return False
    
    def can_increase(self):
        """Check if quantity can be increased"""
        return self.quantity < self.product.stock_quantity
    
    def can_decrease(self):
        """Check if quantity can be decreased"""
        return self.quantity > 1