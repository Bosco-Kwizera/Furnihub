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


def get_or_create_cart(request):
    """Helper function to get or create a cart for the current user/session"""
    cart = None
    
    # If user is authenticated, get their cart
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        # For anonymous users, use session
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
        'cart_total_items': cart.get_total_items(),
        'cart_subtotal': cart.get_subtotal(),
        'cart_tax': cart.get_tax(),
        'cart_total': cart.get_total(),
    }
    return render(request, 'cart/cart.html', context)


@login_required
@require_POST
def add_to_cart(request, product_id):
    """Add item to cart - ONLY for logged-in users"""
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        quantity = int(request.POST.get('quantity', 1))
        
        # Validate quantity
        if quantity < 1:
            messages.error(request, 'Invalid quantity')
            return redirect(request.META.get('HTTP_REFERER', 'products:home'))
        
        if quantity > product.stock_quantity:
            messages.error(request, f'Only {product.stock_quantity} items available')
            return redirect(request.META.get('HTTP_REFERER', 'products:home'))
        
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
        
        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to cart',
                'cart_total_items': cart.get_total_items(),
                'cart_subtotal': str(cart.get_subtotal()),
                'cart_total': str(cart.get_total())
            })
        
        return redirect('cart:cart_view')
        
    except Exception as e:
        messages.error(request, f'Error adding to cart: {str(e)}')
        return redirect(request.META.get('HTTP_REFERER', 'products:home'))


@login_required
@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity - ONLY for logged-in users"""
    try:
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
        
        # Get updated cart for response
        cart = Cart.objects.get(user=request.user)
        
        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_total_items': cart.get_total_items(),
                'cart_subtotal': str(cart.get_subtotal()),
                'cart_tax': str(cart.get_tax()),
                'cart_total': str(cart.get_total())
            })
        
        return redirect('cart:cart_view')
        
    except Exception as e:
        messages.error(request, f'Error updating cart: {str(e)}')
        return redirect('cart:cart_view')


@login_required
@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart - ONLY for logged-in users"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f'{product_name} removed from cart')
        
        # Get updated cart for response
        cart = Cart.objects.get(user=request.user)
        
        # If it's an AJAX request, return JSON response
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{product_name} removed from cart',
                'cart_total_items': cart.get_total_items(),
                'cart_subtotal': str(cart.get_subtotal()),
                'cart_total': str(cart.get_total())
            })
        
        return redirect('cart:cart_view')
        
    except Exception as e:
        messages.error(request, f'Error removing from cart: {str(e)}')
        return redirect('cart:cart_view')


@login_required
@require_POST
def apply_coupon(request):
    """Apply coupon code to cart - ONLY for logged-in users"""
    coupon_code = request.POST.get('coupon_code', '').strip().upper()
    
    if not coupon_code:
        messages.error(request, 'Please enter a coupon code')
        return redirect('cart:cart_view')
    
    # Simple coupon logic - you can expand this
    valid_coupons = {
        'SAVE10': {'discount': 10, 'type': 'percentage'},
        'SAVE20': {'discount': 20, 'type': 'fixed'},
        'FREESHIP': {'discount': 0, 'type': 'shipping'},
    }
    
    if coupon_code in valid_coupons:
        # Store coupon in session
        request.session['coupon_code'] = coupon_code
        request.session['coupon_discount'] = valid_coupons[coupon_code]['discount']
        messages.success(request, f'Coupon "{coupon_code}" applied successfully!')
    else:
        messages.error(request, 'Invalid coupon code')
    
    return redirect('cart:cart_view')


@login_required
@require_POST
def remove_coupon(request):
    """Remove applied coupon"""
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
    if 'coupon_discount' in request.session:
        del request.session['coupon_discount']
    messages.success(request, 'Coupon removed')
    return redirect('cart:cart_view')


# API Views - All require authentication
class CartViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    
    def retrieve(self, request, pk=None):
        """Get current user's cart"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get cart summary"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        data = {
            'total_items': cart.get_total_items(),
            'subtotal': str(cart.get_subtotal()),
            'tax': str(cart.get_tax()),
            'total': str(cart.get_total()),
            'items': [
                {
                    'id': item.id,
                    'product_id': item.product.id,
                    'name': item.product.name,
                    'quantity': item.quantity,
                    'price': str(item.product.price),
                    'total': str(item.get_total_price()),
                    'image': item.product.images.first().image.url if item.product.images.exists() else None
                }
                for item in cart.items.all()
            ]
        }
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart"""
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        try:
            product = get_object_or_404(Product, id=product_id, is_active=True)
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            # Validate stock
            if quantity > product.stock_quantity:
                return Response(
                    {'error': f'Only {product.stock_quantity} items available'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                new_quantity = cart_item.quantity + quantity
                if new_quantity > product.stock_quantity:
                    return Response(
                        {'error': f'Cannot add more than {product.stock_quantity} items'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                cart_item.quantity = new_quantity
                cart_item.save()
            
            serializer = CartSerializer(cart)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def update_item(self, request):
        """Update cart item quantity"""
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            
            if quantity <= 0:
                cart_item.delete()
            else:
                if quantity > cart_item.product.stock_quantity:
                    return Response(
                        {'error': f'Only {cart_item.product.stock_quantity} items available'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                cart_item.quantity = quantity
                cart_item.save()
            
            cart = get_object_or_404(Cart, user=request.user)
            serializer = CartSerializer(cart)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        """Remove item from cart"""
        item_id = request.data.get('item_id')
        
        try:
            cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
            cart_item.delete()
            
            cart = get_object_or_404(Cart, user=request.user)
            serializer = CartSerializer(cart)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Clear cart"""
        try:
            cart = get_object_or_404(Cart, user=request.user)
            cart.clear()
            return Response({'message': 'Cart cleared successfully'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )