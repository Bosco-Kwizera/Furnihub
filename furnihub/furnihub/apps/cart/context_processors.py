from .models import Cart
from apps.products.models import Category
from django.db.models import Count, Q

def cart(request):
    """Add cart data to all templates - Only for authenticated users"""
    cart_items_count = 0
    cart_subtotal = 0
    
    # Only show cart data for authenticated users
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart_items_count = cart.get_total_items()
                cart_subtotal = cart.get_subtotal()
        except Exception as e:
            # If there's any error, just return empty cart
            pass
    
    return {
        'cart_items_count': cart_items_count,
        'cart_subtotal': cart_subtotal,
    }

def categories(request):
    """Add main categories and search query to all templates"""
    # Get only top-level categories (parent is None) that are active
    main_categories = Category.objects.filter(
        parent=None, 
        is_active=True
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('name')
    
    # Get current search query from request
    search_query = request.GET.get('q', '')
    
    return {
        'categories': main_categories,
        'search_query': search_query,
    }