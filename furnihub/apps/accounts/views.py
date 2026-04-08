from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Profile, Address, Wishlist
from .serializers import UserSerializer, ProfileSerializer, AddressSerializer, WishlistSerializer
from apps.orders.models import Order
from apps.products.models import Product


# ==================== WEB VIEWS ====================

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('accounts:register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return redirect('accounts:register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('accounts:register')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', '')
        )
        
        profile = user.profile
        profile.phone = request.POST.get('phone', '')
        profile.newsletter_subscription = request.POST.get('newsletter', False)
        profile.save()
        
        login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('products:home')
    
    return render(request, 'accounts/register.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'products:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out')
    return redirect('products:home')


@login_required
def dashboard_view(request):
    context = {
        'user': request.user,
        'recent_orders': Order.objects.filter(user=request.user)[:5],
        'wishlist_items': Wishlist.objects.filter(user=request.user)[:4],
        'addresses': Address.objects.filter(user=request.user),
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        profile = request.user.profile
        profile.phone = request.POST.get('phone', '')
        profile.birth_date = request.POST.get('birth_date') or None
        profile.newsletter_subscription = request.POST.get('newsletter') == 'on'
        profile.save()
        
        messages.success(request, 'Profile updated successfully')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
def addresses_view(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@login_required
def add_address_view(request):
    if request.method == 'POST':
        address = Address.objects.create(
            user=request.user,
            address_type=request.POST.get('address_type'),
            full_name=request.POST.get('full_name'),
            phone=request.POST.get('phone'),
            address_line1=request.POST.get('address_line1'),
            address_line2=request.POST.get('address_line2', ''),
            city=request.POST.get('city'),
            state=request.POST.get('state'),
            postal_code=request.POST.get('postal_code'),
            country=request.POST.get('country'),
            is_default=request.POST.get('is_default') == 'on'
        )
        messages.success(request, 'Address added successfully')
        return redirect('accounts:addresses')
    
    return render(request, 'accounts/add_address.html')


@login_required
def edit_address_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.address_type = request.POST.get('address_type')
        address.full_name = request.POST.get('full_name')
        address.phone = request.POST.get('phone')
        address.address_line1 = request.POST.get('address_line1')
        address.address_line2 = request.POST.get('address_line2', '')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.postal_code = request.POST.get('postal_code')
        address.country = request.POST.get('country')
        address.is_default = request.POST.get('is_default') == 'on'
        address.save()
        
        messages.success(request, 'Address updated successfully')
        return redirect('accounts:addresses')
    
    return render(request, 'accounts/edit_address.html', {'address': address})


@login_required
def delete_address_view(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, 'Address deleted successfully')
    return redirect('accounts:addresses')


@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            wishlist_item.delete()
            messages.info(request, f'{product.name} removed from wishlist')
        else:
            messages.success(request, f'{product.name} added to wishlist')
        
        return redirect(request.META.get('HTTP_REFERER', 'products:home'))
    
    return render(request, 'accounts/wishlist.html', {'wishlist': wishlist_items})


@login_required
def orders_view(request):
    # FIXED: Changed from 'order_date' to 'created_at'
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/orders.html', {'orders': orders})


# ==================== API VIEWS ====================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'])
    def update_profile(self, request):
        serializer = ProfileSerializer(request.user.profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(old_password):
            return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully'})
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'})
        except Exception:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        address = self.get_object()
        address.is_default = True
        address.save()
        return Response({'message': 'Default address set'})


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        Wishlist.objects.filter(user=request.user).delete()
        return Response({'message': 'Wishlist cleared'})