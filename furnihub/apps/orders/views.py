from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, OrderItem, OrderStatusHistory
from apps.cart.models import Cart
from apps.accounts.models import Address
from apps.products.models import Product
from .serializers import OrderSerializer, OrderCreateSerializer
import json
from decimal import Decimal


@login_required
def checkout_view(request):
    """Checkout page"""
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty')
        return redirect('products:home')
    
    if cart.get_total_items() == 0:
        messages.warning(request, 'Your cart is empty')
        return redirect('products:home')
    
    addresses = Address.objects.filter(user=request.user)
    
    context = {
        'cart': cart,
        'addresses': addresses,
        'default_address': addresses.filter(is_default=True).first(),
    }
    return render(request, 'orders/checkout.html', context)


@login_required
@transaction.atomic
def place_order(request):
    """Place an order from cart"""
    if request.method != 'POST':
        return redirect('cart:cart_view')
    
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        messages.error(request, 'Your cart is empty')
        return redirect('products:home')
    
    if cart.get_total_items() == 0:
        messages.error(request, 'Your cart is empty')
        return redirect('products:home')
    
    # Get shipping address
    address_id = request.POST.get('address_id')
    
    if address_id and address_id != 'new':
        # Use existing address
        try:
            address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            messages.error(request, 'Selected address not found')
            return redirect('orders:checkout')
    else:
        # Validate new address fields
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address_line1 = request.POST.get('address_line1', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()
        country = request.POST.get('country', 'United States').strip()
        
        # Check required fields
        errors = []
        if not full_name:
            errors.append('Full name is required')
        if not phone:
            errors.append('Phone number is required')
        if not address_line1:
            errors.append('Address is required')
        if not city:
            errors.append('City is required')
        if not state:
            errors.append('State is required')
        if not postal_code:
            errors.append('Postal code is required')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('orders:checkout')
        
        # Create new address
        try:
            address = Address.objects.create(
                user=request.user,
                address_type=request.POST.get('address_type', 'home'),
                full_name=full_name,
                phone=phone,
                address_line1=address_line1,
                address_line2=request.POST.get('address_line2', ''),
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                is_default=request.POST.get('is_default') == 'on'
            )
        except Exception as e:
            messages.error(request, f'Error creating address: {str(e)}')
            return redirect('orders:checkout')
    
    # Get payment method from POST data
    payment_method = request.POST.get('payment_method', 'cash_on_delivery')
    
    # Get mobile money details if applicable
    mobile_money_provider = None
    mobile_number = None
    
    if payment_method == 'mobile_money':
        mobile_money_provider = request.POST.get('mobile_money_provider')
        mobile_number = request.POST.get('mobile_number')
    
    # Calculate totals
    subtotal = cart.get_subtotal()
    tax = cart.get_tax()
    shipping_cost = Decimal('0.00')
    total = subtotal + tax + shipping_cost
    
    # Determine payment status based on payment method
    if payment_method == 'cash_on_delivery':
        payment_status = 'pending'
    elif payment_method == 'mobile_money':
        payment_status = 'pending'  # Change to 'paid' if payment is instant
    else:
        payment_status = 'pending'
    
    # Create order
    try:
        order = Order.objects.create(
            user=request.user,
            subtotal=subtotal,
            tax=tax,
            shipping_cost=shipping_cost,
            total=total,
            shipping_address=address,
            shipping_name=address.full_name,
            shipping_phone=address.phone,
            notes=request.POST.get('notes', ''),
            payment_method=payment_method,
            payment_status=payment_status,
            mobile_money_provider=mobile_money_provider,
            mobile_number=mobile_number,
        )
    except Exception as e:
        messages.error(request, f'Error creating order: {str(e)}')
        return redirect('orders:checkout')
    
    # Create order items
    for cart_item in cart.items.select_related('product').all():
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            price=cart_item.product.price,
            total=cart_item.get_total_price()
        )
        
        # Update stock
        product = cart_item.product
        product.stock_quantity -= cart_item.quantity
        product.save()
    
    # Create status history
    OrderStatusHistory.objects.create(
        order=order,
        status='pending',
        note='Order placed successfully',
        created_by=request.user
    )
    
    # Clear cart
    cart.clear()
    
    messages.success(request, f'Order #{order.order_number} placed successfully!')
    return redirect('orders:order_confirmation', order_id=order.id)


@login_required
def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/confirmation.html', {'order': order})


@login_required
def order_detail(request, order_id):
    """Order detail page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/detail.html', {'order': order})


@login_required
def order_tracking(request, order_id):
    """Order tracking page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/tracking.html', {'order': order})


@login_required
@transaction.atomic
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_be_cancelled():
        messages.error(request, 'This order cannot be cancelled')
        return redirect('orders:order_detail', order_id=order.id)
    
    # Restore stock
    for item in order.items.all():
        product = item.product
        product.stock_quantity += item.quantity
        product.save()
    
    order.status = 'cancelled'
    order.save()
    
    OrderStatusHistory.objects.create(
        order=order,
        status='cancelled',
        note='Order cancelled by customer',
        created_by=request.user
    )
    
    messages.success(request, f'Order #{order.order_number} cancelled successfully')
    return redirect('orders:order_detail', order_id=order.id)


# API Views
class OrderViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get cart
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        if cart.get_total_items() == 0:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create address
        address_id = serializer.validated_data.get('address_id')
        if address_id:
            try:
                address = Address.objects.get(id=address_id, user=request.user)
            except Address.DoesNotExist:
                return Response({'error': 'Address not found'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            address_data = serializer.validated_data.get('address')
            if not address_data:
                return Response({'error': 'Address data is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate address data
            required_fields = ['full_name', 'phone', 'address_line1', 'city', 'state', 'postal_code']
            for field in required_fields:
                if not address_data.get(field):
                    return Response({'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            address = Address.objects.create(user=request.user, **address_data)
        
        # Get payment method data
        payment_method = serializer.validated_data.get('payment_method', 'cash_on_delivery')
        mobile_money_provider = serializer.validated_data.get('mobile_money_provider')
        mobile_number = serializer.validated_data.get('mobile_number')
        
        # Calculate totals
        subtotal = cart.get_subtotal()
        tax = cart.get_tax()
        shipping_cost = Decimal(str(serializer.validated_data.get('shipping_cost', 0)))
        total = subtotal + tax + shipping_cost
        
        # Determine payment status
        payment_status = 'pending'
        
        # Create order
        order = Order.objects.create(
            user=request.user,
            subtotal=subtotal,
            tax=tax,
            shipping_cost=shipping_cost,
            total=total,
            shipping_address=address,
            shipping_name=address.full_name,
            shipping_phone=address.phone,
            notes=serializer.validated_data.get('notes', ''),
            payment_method=payment_method,
            payment_status=payment_status,
            mobile_money_provider=mobile_money_provider,
            mobile_number=mobile_number,
        )
        
        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price,
                total=cart_item.get_total_price()
            )
            
            # Update stock
            product = cart_item.product
            product.stock_quantity -= cart_item.quantity
            product.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='pending',
            note='Order placed via API',
            created_by=request.user
        )
        
        # Clear cart
        cart.clear()
        
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        if not order.can_be_cancelled():
            return Response({'error': 'Order cannot be cancelled'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Restore stock
        with transaction.atomic():
            for item in order.items.all():
                product = item.product
                product.stock_quantity += item.quantity
                product.save()
            
            order.status = 'cancelled'
            order.save()
            
            OrderStatusHistory.objects.create(
                order=order,
                status='cancelled',
                note='Order cancelled via API',
                created_by=request.user
            )
        
        return Response({'message': 'Order cancelled successfully'})
    
    @action(detail=True, methods=['get'])
    def track(self, request, pk=None):
        order = self.get_object()
        history = order.status_history.all()
        data = {
            'order_number': order.order_number,
            'status': order.status,
            'tracking_number': order.tracking_number,
            'history': [
                {
                    'status': h.status,
                    'note': h.note,
                    'created_at': h.created_at
                }
                for h in history
            ]
        }
        return Response(data)