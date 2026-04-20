import django_filters
from django.db import models
from .models import Product, Category


class ProductFilter(django_filters.FilterSet):
    """Filter for products"""
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.ModelChoiceFilter(
        field_name='category',
        queryset=Category.objects.filter(is_active=True)
    )
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    has_discount = django_filters.BooleanFilter(method='filter_has_discount')
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    class Meta:
        model = Product
        fields = {
            'category': ['exact'],
            'brand': ['exact', 'icontains'],
            'color': ['exact', 'icontains'],
            'material': ['exact', 'icontains'],
            'price': ['lt', 'gt', 'lte', 'gte'],
            'is_featured': ['exact'],
            'is_active': ['exact'],
        }
    
    def filter_in_stock(self, queryset, name, value):
        """Filter products that are in stock"""
        if value:
            return queryset.filter(stock_quantity__gt=0)
        return queryset
    
    def filter_has_discount(self, queryset, name, value):
        """Filter products that have a discount"""
        if value:
            return queryset.filter(compare_price__isnull=False, compare_price__gt=models.F('price'))
        return queryset