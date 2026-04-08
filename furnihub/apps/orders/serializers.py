from rest_framework import serializers
from .models import Order, OrderItem, OrderStatusHistory
from apps.accounts.serializers import AddressSerializer
from apps.accounts.models import Address
from apps.products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price', 'total']

class OrderStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusHistory
        fields = ['status', 'note', 'created_at']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    shipping_address = AddressSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_number', 'user', 'status', 'payment_status',
                  'subtotal', 'tax', 'shipping_cost', 'total', 'shipping_address',
                  'shipping_name', 'shipping_phone', 'tracking_number', 'notes',
                  'items', 'status_history', 'created_at', 'updated_at']
        read_only_fields = ['order_number', 'created_at', 'updated_at']

class OrderCreateSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=False)
    address = serializers.DictField(required=False)
    shipping_cost = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if not data.get('address_id') and not data.get('address'):
            raise serializers.ValidationError("Either address_id or address must be provided")
        
        if data.get('address'):
            # Validate address fields
            required_fields = ['full_name', 'phone', 'address_line1', 'city', 'state', 'postal_code', 'country']
            for field in required_fields:
                if field not in data['address']:
                    raise serializers.ValidationError(f"Address missing required field: {field}")
        
        return data