from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from apps.products.models import Product, Category, ProductImage
from apps.orders.models import Order
from django.contrib.auth.models import User
from decimal import Decimal

def admin_required(view_func):
    """Decorator to check if user is admin/superuser"""
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_superuser,
        login_url='/accounts/login/'
    )
    return actual_decorator(view_func)

@admin_required
def dashboard(request):
    """Admin dashboard home"""
    # Get statistics
    total_orders = Order.objects.count()
    total_products = Product.objects.count()
    total_users = User.objects.count()
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(Sum('total'))['total__sum'] or Decimal('0')
    
    # Recent orders
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    # Low stock products
    low_stock = Product.objects.filter(stock_quantity__lt=10, is_active=True)[:5]
    
    # Orders by status
    orders_by_status = {
        'pending': Order.objects.filter(status='pending').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'shipped': Order.objects.filter(status='shipped').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }
    
    # Recent activity
    recent_activity = []
    
    # Get recent orders
    for order in Order.objects.order_by('-created_at')[:10]:
        recent_activity.append({
            'type': 'order',
            'message': f'New order #{order.order_number} - ${order.total}',
            'time': order.created_at,
            'order_id': order.id
        })
    
    context = {
        'total_orders': total_orders,
        'total_products': total_products,
        'total_users': total_users,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'low_stock': low_stock,
        'orders_by_status': orders_by_status,
        'recent_activity': recent_activity[:10],
    }
    return render(request, 'admin_dashboard/dashboard.html', context)

@admin_required
def orders_list(request):
    """List all orders"""
    status_filter = request.GET.get('status', '')
    orders = Order.objects.all().order_by('-created_at')
    
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'admin_dashboard/orders_list.html', context)

@admin_required
def order_detail(request, order_id):
    """View order details"""
    order = get_object_or_404(Order, id=order_id)
    context = {'order': order}
    return render(request, 'admin_dashboard/order_detail.html', context)

@admin_required
def update_order_status(request, order_id):
    """Update order status"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        messages.success(request, f'Order #{order.order_number} status updated to {order.get_status_display()}')
    return redirect('admin_dashboard:order_detail', order_id=order_id)

@admin_required
def products_list(request):
    """List all products"""
    products = Product.objects.all().order_by('-created_at')
    context = {'products': products}
    return render(request, 'admin_dashboard/products_list.html', context)

@admin_required
def add_product(request):
    """Add new product"""
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        stock_quantity = request.POST.get('stock_quantity')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        
        # Create product
        product = Product.objects.create(
            name=name,
            category_id=category_id,
            price=price,
            stock_quantity=stock_quantity,
            description=description,
            is_active=is_active,
            is_featured=is_featured
        )
        
        # Handle images
        images = request.FILES.getlist('images')
        for i, image in enumerate(images):
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=(i == 0),
                order=i
            )
        
        messages.success(request, f'Product "{product.name}" added successfully!')
        return redirect('admin_dashboard:products_list')
    
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'admin_dashboard/product_form.html', context)

@admin_required
def edit_product(request, product_id):
    """Edit product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category')
        product.price = request.POST.get('price')
        product.stock_quantity = request.POST.get('stock_quantity')
        product.description = request.POST.get('description')
        product.is_active = request.POST.get('is_active') == 'on'
        product.is_featured = request.POST.get('is_featured') == 'on'
        product.save()
        
        # Handle new images
        images = request.FILES.getlist('images')
        for image in images:
            ProductImage.objects.create(
                product=product,
                image=image,
                is_primary=False
            )
        
        messages.success(request, f'Product "{product.name}" updated successfully!')
        return redirect('admin_dashboard:products_list')
    
    categories = Category.objects.all()
    context = {'product': product, 'categories': categories}
    return render(request, 'admin_dashboard/product_form.html', context)

@admin_required
def delete_product(request, product_id):
    """Delete product"""
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
    return redirect('admin_dashboard:products_list')

@admin_required
def categories_list(request):
    """List all categories"""
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'admin_dashboard/categories_list.html', context)

@admin_required
def add_category(request):
    """Add new category"""
    if request.method == 'POST':
        name = request.POST.get('name')
        parent_id = request.POST.get('parent')
        description = request.POST.get('description')
        
        Category.objects.create(
            name=name,
            parent_id=parent_id if parent_id else None,
            description=description
        )
        messages.success(request, f'Category "{name}" added successfully!')
        return redirect('admin_dashboard:categories_list')
    
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'admin_dashboard/category_form.html', context)

@admin_required
def users_list(request):
    """List all users"""
    users = User.objects.all().order_by('-date_joined')
    context = {'users': users}
    return render(request, 'admin_dashboard/users_list.html', context)