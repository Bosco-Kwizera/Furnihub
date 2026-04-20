from .models import Cart
from apps.products.models import Category
from apps.accounts.models import Wishlist

def cart(request):
    """Add cart data to all templates"""
    cart_items_count = 0
    cart_subtotal = 0
    
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_items_count = cart.get_total_items()
            cart_subtotal = cart.get_subtotal()
    
    return {
        'cart_items_count': cart_items_count,
        'cart_subtotal': cart_subtotal,
    }

def categories(request):
    """Add categories to all templates"""
    categories = Category.objects.filter(parent=None, is_active=True)
    return {
        'categories': categories,
        'search_query': request.GET.get('q', '')
    }

def wishlist_count(request):
    """Add wishlist count to all templates"""
    count = 0
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
    return {'wishlist_count': count}