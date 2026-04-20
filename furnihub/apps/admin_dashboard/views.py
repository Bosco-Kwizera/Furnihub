from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from apps.products.models import Product, Category, ProductImage
from apps.orders.models import Order
from django.contrib.auth.models import User, Group, Permission
from django.http import JsonResponse
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
        short_description = request.POST.get('short_description', '')
        brand = request.POST.get('brand', '')
        material = request.POST.get('material', '')
        color = request.POST.get('color', '')
        dimensions = request.POST.get('dimensions', '')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        
        # Create product
        product = Product.objects.create(
            name=name,
            category_id=category_id,
            price=price,
            stock_quantity=stock_quantity,
            description=description,
            short_description=short_description,
            brand=brand,
            material=material,
            color=color,
            dimensions=dimensions,
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
        product.short_description = request.POST.get('short_description', '')
        product.brand = request.POST.get('brand', '')
        product.material = request.POST.get('material', '')
        product.color = request.POST.get('color', '')
        product.dimensions = request.POST.get('dimensions', '')
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


# ==================== USER MANAGEMENT VIEWS ====================

@admin_required
def users_list(request):
    """List all users with options to manage roles"""
    users = User.objects.all().order_by('-date_joined')
    
    # Get all available groups/roles
    groups = Group.objects.all()
    
    context = {
        'users': users,
        'groups': groups,
    }
    return render(request, 'admin_dashboard/users_list.html', context)


@admin_required
def user_detail(request, user_id):
    """View and edit user details"""
    user_obj = get_object_or_404(User, id=user_id)
    groups = Group.objects.all()
    
    if request.method == 'POST':
        # Update basic info
        user_obj.first_name = request.POST.get('first_name', '')
        user_obj.last_name = request.POST.get('last_name', '')
        user_obj.email = request.POST.get('email', '')
        user_obj.is_active = request.POST.get('is_active') == 'on'
        user_obj.is_staff = request.POST.get('is_staff') == 'on'
        user_obj.is_superuser = request.POST.get('is_superuser') == 'on'
        user_obj.save()
        
        # Update groups
        user_obj.groups.clear()
        group_ids = request.POST.getlist('groups')
        for group_id in group_ids:
            group = Group.objects.get(id=group_id)
            user_obj.groups.add(group)
        
        messages.success(request, f'User "{user_obj.username}" updated successfully!')
        return redirect('admin_dashboard:users_list')
    
    context = {
        'user_obj': user_obj,
        'groups': groups,
        'user_groups': user_obj.groups.all(),
    }
    return render(request, 'admin_dashboard/user_detail.html', context)


@admin_required
def user_roles(request):
    """Manage user roles and groups"""
    groups = Group.objects.all()
    
    if request.method == 'POST':
        # Create new group
        if 'create_group' in request.POST:
            group_name = request.POST.get('group_name')
            if group_name:
                group, created = Group.objects.get_or_create(name=group_name)
                if created:
                    messages.success(request, f'Group "{group_name}" created successfully!')
                else:
                    messages.error(request, f'Group "{group_name}" already exists!')
        
        # Delete group
        elif 'delete_group' in request.POST:
            group_id = request.POST.get('group_id')
            group = get_object_or_404(Group, id=group_id)
            group_name = group.name
            group.delete()
            messages.success(request, f'Group "{group_name}" deleted successfully!')
        
        # Update group permissions
        elif 'update_permissions' in request.POST:
            group_id = request.POST.get('group_id')
            group = get_object_or_404(Group, id=group_id)
            permission_ids = request.POST.getlist('permissions')
            group.permissions.clear()
            for perm_id in permission_ids:
                perm = Permission.objects.get(id=perm_id)
                group.permissions.add(perm)
            messages.success(request, f'Permissions for "{group.name}" updated successfully!')
        
        return redirect('admin_dashboard:user_roles')
    
    # Get all permissions grouped by app
    permissions_by_app = {}
    for perm in Permission.objects.all().order_by('content_type__app_label', 'codename'):
        app_label = perm.content_type.app_label
        if app_label not in permissions_by_app:
            permissions_by_app[app_label] = []
        permissions_by_app[app_label].append({
            'id': perm.id,
            'name': perm.name,
            'codename': perm.codename
        })
    
    context = {
        'groups': groups,
        'permissions_by_app': permissions_by_app,
    }
    return render(request, 'admin_dashboard/user_roles.html', context)


@admin_required
def toggle_user_status(request, user_id):
    """Activate/Deactivate user account"""
    user_obj = get_object_or_404(User, id=user_id)
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    
    status = "activated" if user_obj.is_active else "deactivated"
    messages.success(request, f'User "{user_obj.username}" has been {status}.')
    return redirect('admin_dashboard:users_list')


@admin_required
def make_staff(request, user_id):
    """Make a user staff member"""
    user_obj = get_object_or_404(User, id=user_id)
    user_obj.is_staff = True
    user_obj.save()
    messages.success(request, f'User "{user_obj.username}" is now a staff member.')
    return redirect('admin_dashboard:users_list')


@admin_required
def make_superuser(request, user_id):
    """Make a user superuser"""
    user_obj = get_object_or_404(User, id=user_id)
    user_obj.is_superuser = True
    user_obj.is_staff = True
    user_obj.save()
    messages.success(request, f'User "{user_obj.username}" is now a superuser.')
    return redirect('admin_dashboard:users_list')


@admin_required
def remove_staff(request, user_id):
    """Remove staff status from user"""
    user_obj = get_object_or_404(User, id=user_id)
    user_obj.is_staff = False
    user_obj.is_superuser = False
    user_obj.save()
    messages.success(request, f'Staff status removed from "{user_obj.username}".')
    return redirect('admin_dashboard:users_list')


@admin_required
def get_group_permissions(request, group_id):
    """API endpoint to get permissions for a group"""
    group = get_object_or_404(Group, id=group_id)
    permissions = list(group.permissions.values_list('id', flat=True))
    return JsonResponse({'permissions': permissions})