from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, ProductReview

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'product_count']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'slug', 'parent', 'description')
        }),
        ('Display Settings', {
            'fields': ('image', 'is_active')
        }),
    )
    
    def product_count(self, obj):
        """Count products in this category"""
        count = obj.products.count()
        return count
    product_count.short_description = 'Products'

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ['image', 'alt_text', 'is_primary', 'order']
    
    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'

class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ['user', 'rating', 'title', 'comment', 'created_at']
    can_delete = True
    fields = ['user', 'rating', 'title', 'comment', 'is_approved', 'created_at']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock_quantity', 'is_active', 'is_featured']
    list_filter = ['category', 'is_active', 'is_featured', 'brand']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['sku', 'created_at', 'updated_at']
    list_editable = ['price', 'stock_quantity', 'is_active', 'is_featured']
    inlines = [ProductImageInline, ProductReviewInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'slug', 'sku', 'description', 'short_description')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'is_active', 'is_featured')
        }),
        ('Product Details', {
            'fields': ('brand', 'material', 'color', 'dimensions', 'weight')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'is_primary', 'order']
    list_filter = ['is_primary', 'product__category']
    search_fields = ['product__name', 'alt_text']
    
    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'title', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['product__name', 'user__username', 'title', 'comment']
    actions = ['approve_reviews', 'unapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"
    
    def unapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    unapprove_reviews.short_description = "Unapprove selected reviews"

# Register Category
admin.site.register(Category, CategoryAdmin)