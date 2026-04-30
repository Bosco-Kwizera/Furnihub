from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusHistory

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'price', 'total']

class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['status', 'note', 'created_by', 'created_at']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'total', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email', 'shipping_name']
    readonly_fields = ['order_number', 'subtotal', 'tax', 'shipping_cost', 'total', 'created_at', 'updated_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax', 'shipping_cost', 'total')
        }),
        ('Shipping Information', {
            'fields': ('shipping_name', 'shipping_phone', 'shipping_address')
        }),
        ('Tracking', {
            'fields': ('tracking_number', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'cancel_orders']
    
    def mark_as_processing(self, request, queryset):
        queryset.update(status='processing')
        for order in queryset:
            OrderStatusHistory.objects.create(
                order=order,
                status='processing',
                note='Status updated via admin',
                created_by=request.user
            )
    mark_as_processing.short_description = "Mark selected orders as processing"
    
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
        for order in queryset:
            OrderStatusHistory.objects.create(
                order=order,
                status='shipped',
                note='Status updated via admin',
                created_by=request.user
            )
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
        for order in queryset:
            OrderStatusHistory.objects.create(
                order=order,
                status='delivered',
                note='Status updated via admin',
                created_by=request.user
            )
    mark_as_delivered.short_description = "Mark selected orders as delivered"
    
    def cancel_orders(self, request, queryset):
        queryset.update(status='cancelled')
        for order in queryset:
            OrderStatusHistory.objects.create(
                order=order,
                status='cancelled',
                note='Order cancelled via admin',
                created_by=request.user
            )
    cancel_orders.short_description = "Cancel selected orders"

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price', 'total']
    list_filter = ['order__status']
    search_fields = ['order__order_number', 'product__name']

@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['order', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_number', 'note']