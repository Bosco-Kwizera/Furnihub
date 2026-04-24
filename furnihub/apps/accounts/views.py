from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Profile, Address, Wishlist
from .serializers import UserSerializer, ProfileSerializer, AddressSerializer, WishlistSerializer
from apps.orders.models import Order
from apps.products.models import Product


# ==================== PASSWORD VALIDATION HELPER ====================

def validate_strong_password(password):
    """Validate that password meets security requirements"""
    errors = []
    
    # Check minimum length
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')
    
    # Check for uppercase letter
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')
    
    # Check for lowercase letter
    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')
    
    # Check for digit
    if not re.search(r'\d', password):
        errors.append('Password must contain at least one number')
    
    # Check for special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append('Password must contain at least one special character (!@#$%^&*)')
    
    # Check for common passwords
    common_passwords = [
        'password', '12345678', 'qwerty123', 'admin123', 
        'letmein', 'welcome123', 'password123', 'abc12345',
        'Password123', 'Pass@123', 'Admin@123'
    ]
    if password.lower() in common_passwords:
        errors.append('Password is too common. Please choose a more secure password')
    
    return errors


# ==================== WEB VIEWS ====================

def register_view(request):
    """Register a new user with strong password validation"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return redirect('accounts:register')
        
        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return redirect('accounts:register')
        
        # Check if email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return redirect('accounts:register')
        
        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please enter a valid email address')
            return redirect('accounts:register')
        
        # Validate strong password
        password_errors = validate_strong_password(password)
        if password_errors:
            for error in password_errors:
                messages.error(request, error)
            return redirect('accounts:register')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', '')
        )
        
        # Update profile
        profile = user.profile
        profile.phone = request.POST.get('phone', '')
        profile.newsletter_subscription = request.POST.get('newsletter', False)
        profile.save()
        
        # Login user
        login(request, user)
        messages.success(request, 'Registration successful! Your account is secure.')
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
    """View and manage wishlist"""
    
    # Handle POST request (adding/removing items)
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        # Check if product already in wishlist
        wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()
        
        if wishlist_item:
            # Remove from wishlist
            wishlist_item.delete()
            messages.success(request, f'{product.name} removed from your wishlist.')
        else:
            # Add to wishlist
            Wishlist.objects.create(user=request.user, product=product)
            messages.success(request, f'{product.name} added to your wishlist!')
        
        # Redirect back to the same page
        next_url = request.POST.get('next', request.META.get('HTTP_REFERER', 'products:home'))
        return redirect(next_url)
    
    # Handle GET request (display wishlist)
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product__category')
    
    context = {
        'wishlist': wishlist_items,
        'wishlist_count': wishlist_items.count(),
    }
    return render(request, 'accounts/wishlist.html', context)


@login_required
def orders_view(request):
    # FIXED: Changed from 'order_date' to 'created_at'
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/orders.html', {'orders': orders})


# ==================== PASSWORD RESET VIEWS (Optional) ====================

@login_required
def change_password_view(request):
    """Allow users to change their password"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Check old password
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect')
            return redirect('accounts:change_password')
        
        # Check if new passwords match
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match')
            return redirect('accounts:change_password')
        
        # Validate strong password
        password_errors = validate_strong_password(new_password)
        if password_errors:
            for error in password_errors:
                messages.error(request, error)
            return redirect('accounts:change_password')
        
        # Change password
        request.user.set_password(new_password)
        request.user.save()
        
        messages.success(request, 'Your password has been changed successfully! Please login again.')
        return redirect('accounts:login')
    
    return render(request, 'accounts/change_password.html')


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
        
        # Validate strong password for API
        password_errors = validate_strong_password(new_password)
        if password_errors:
            return Response({'errors': password_errors}, status=status.HTTP_400_BAD_REQUEST)
        
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