from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Cart, CartItem
from apps.products.models import Product
from .serializers import CartSerializer, CartItemSerializer
import uuid

# Note: This function is kept for reference but not used for adding to cart
def get_or_create_cart(request):
    """Helper function to get or create a cart for the current user/session"""
    cart = None
    
    # If user is authenticated, get their cart
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For anonymous users, use session (read-only)
        session_id = request.session.get('cart_session_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            request.session['cart_session_id'] = session_id
        
        cart, created = Cart.objects.get_or_create(session_id=session_id)
    
    return cart

@login_required
def cart_view(request):
    """Display cart contents - Only logged-in users can view cart"""
    # Get or create cart for logged-in user
    cart, created = Cart.objects.get_or_create(user=request.user)
    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('product').all(),
    }
    return render(request, 'cart/cart.html', context)

@login_required  # Only logged-in users can add to cart
@require_POST
def add_to_cart(request, product_id):
    """Add item to cart - ONLY for logged-in users"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    # Validate quantity
    if quantity < 1:
        messages.error(request, 'Invalid quantity')
        return redirect('products:product_detail', 
                       category_slug=product.category.slug, 
                       product_slug=product.slug)
    
    if quantity > product.stock_quantity:
        messages.error(request, f'Only {product.stock_quantity} items available')
        return redirect('products:product_detail', 
                       category_slug=product.category.slug, 
                       product_slug=product.slug)
    
    # Get or create cart for logged-in user
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Add or update cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock_quantity:
            messages.error(request, f'Cannot add more than {product.stock_quantity} items')
        else:
            cart_item.quantity = new_quantity
            cart_item.save()
            messages.success(request, f'{product.name} quantity updated in cart')
    else:
        messages.success(request, f'{product.name} added to cart')
    
    return redirect('cart:cart_view')

@login_required  # Only logged-in users can update cart
@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity - ONLY for logged-in users"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        cart_item.delete()
        messages.success(request, f'{cart_item.product.name} removed from cart')
    elif quantity > cart_item.product.stock_quantity:
        messages.error(request, f'Only {cart_item.product.stock_quantity} items available')
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f'{cart_item.product.name} quantity updated')
    
    return redirect('cart:cart_view')

@login_required  # Only logged-in users can remove from cart
@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart - ONLY for logged-in users"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'{product_name} removed from cart')
    return redirect('cart:cart_view')

@login_required
@require_POST
def apply_coupon(request):
    """Apply coupon code to cart - ONLY for logged-in users"""
    coupon_code = request.POST.get('coupon_code')
    # Implement coupon logic here
    messages.error(request, 'Invalid coupon code')
    return redirect('cart:cart_view')

# API Views - All require authentication
class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def retrieve(self, request, pk=None):
        """Get current user's cart"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart"""
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_item(self, request):
        """Update cart item quantity"""
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()
        
        cart = get_object_or_404(Cart, user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Remove item from cart"""
        item_id = request.data.get('item_id')
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        
        cart = get_object_or_404(Cart, user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear cart"""
        cart = get_object_or_404(Cart, user=request.user)
        cart.clear()
        return Response({'message': 'Cart cleared'})