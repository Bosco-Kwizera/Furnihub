from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Address, Wishlist

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone', 'birth_date', 'profile_image', 'newsletter_subscription']

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name',
                  'profile', 'date_joined', 'last_login']
        read_only_fields = ['date_joined', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'address_type', 'full_name', 'phone', 'address_line1',
                  'address_line2', 'city', 'state', 'postal_code', 'country',
                  'is_default', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class WishlistSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
    product_image = serializers.ImageField(source='product.images.filter(is_primary=True).first', read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_name', 'product_price', 'product_image', 'created_at']
        read_only_fields = ['created_at']