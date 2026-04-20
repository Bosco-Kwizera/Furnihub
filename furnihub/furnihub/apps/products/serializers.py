from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductReview

class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.IntegerField(source='products.count', read_only=True)
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'parent', 
                  'children', 'product_count', 'is_active']
    
    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'order']

class ProductReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = ['id', 'user', 'user_name', 'rating', 'title', 'comment', 
                  'is_approved', 'created_at']
        read_only_fields = ['user', 'is_approved']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'category', 'category_name', 'description',
                  'short_description', 'price', 'compare_price', 'discount_percentage',
                  'sku', 'stock_quantity', 'is_active', 'is_featured', 'brand',
                  'material', 'color', 'dimensions', 'weight', 'images', 'reviews',
                  'average_rating', 'created_at', 'updated_at']
    
    def get_reviews(self, obj):
        reviews = obj.reviews.filter(is_approved=True)[:5]
        return ProductReviewSerializer(reviews, many=True).data
    
    def get_average_rating(self, obj):
        avg = obj.reviews.filter(is_approved=True).aggregate(
            avg=serializers.models.Avg('rating')
        )['avg']
        return round(avg, 1) if avg else 0
    
    def get_discount_percentage(self, obj):
        return obj.get_discount_percentage()