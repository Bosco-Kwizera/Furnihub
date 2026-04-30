from rest_framework import serializers
from .models import Payment, PaymentLog
from apps.orders.serializers import OrderSerializer

class PaymentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = ['event_type', 'message', 'data', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    logs = PaymentLogSerializer(many=True, read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'user', 'order', 'transaction_id', 'payment_method',
                  'payment_status', 'amount', 'currency', 'gateway_reference',
                  'logs', 'created_at', 'completed_at']
        read_only_fields = ['transaction_id', 'created_at', 'completed_at']