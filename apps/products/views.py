from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.db.models import Q, Count, Avg, Min, Max
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
# from django_filters.rest_framework import DjangoFilterBackend  # Commented out for compatibility

from .models import Category, Product, ProductImage, ProductReview
from .serializers import ProductSerializer, CategorySerializer, ProductReviewSerializer
# from .filters import ProductFilter  # Commented out for compatibility


# ==================== WEB VIEWS ====================

class HomeView(ListView):
    """Home page view - displays featured products and categories"""
    model = Product
    template_name = 'products/home.html'
    context_object_name = 'products'
    
    def get_queryset(self):
        # Get featured products
        return Product.objects.filter(is_active=True, is_featured=True)[:8]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all parent categories for navigation
        context['categories'] = Category.objects.filter(parent=None, is_active=True)
        
        # Get featured categories
        context['featured_categories'] = Category.objects.filter(
            is_active=True
        ).annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0)[:6]
        
        # Get new arrivals
        context['new_arrivals'] = Product.objects.filter(
            is_active=True
        ).order_by('-created_at')[:4]
        
        return context
    
class CategoryDetailView(ListView):
    """Simple category detail view - shows all products in a category"""
    model = Product
    template_name = 'products/category_products.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        # Get the category from URL
        category_slug = self.kwargs.get('category_slug')
        self.current_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        
        # Get all products in this category
        # This includes products from this category and all its subcategories
        category_ids = [self.current_category.id]
        
        # Add all child category IDs
        for child in self.current_category.children.all():
            category_ids.append(child.id)
            # Add grandchild categories if any
            for grandchild in child.children.all():
                category_ids.append(grandchild.id)
        
        # Get products
        products = Product.objects.filter(
            category_id__in=category_ids,
            is_active=True
        )
        
        # Apply sorting if needed
        sort_by = self.request.GET.get('sort')
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        
        return products
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.current_category
        context['total_products'] = self.get_queryset().count()
        context['current_sort'] = self.request.GET.get('sort', '')
        return context    


class ProductListView(ListView):
    """Product list page with filtering and search"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        # Start with all active products
        queryset = Product.objects.filter(is_active=True)
        
        # Get category slug from URL
        category_slug = self.kwargs.get('category_slug')
        
        # Apply category filter if provided
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug, is_active=True)
            self.current_category = category
            
            # Get products from this category and its subcategories
            if category.children.exists():
                # Get all subcategory IDs
                child_categories = category.children.values_list('id', flat=True)
                category_ids = list(child_categories) + [category.id]
                queryset = queryset.filter(category_id__in=category_ids)
            else:
                queryset = queryset.filter(category=category)
        
        # Apply search filter
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(brand__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Apply price range filters
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        # Apply brand filter
        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(brand=brand)
        
        # Apply color filter
        color = self.request.GET.get('color')
        if color:
            queryset = queryset.filter(color=color)
        
        # Apply material filter
        material = self.request.GET.get('material')
        if material:
            queryset = queryset.filter(material=material)
        
        # Apply sorting
        sort_by = self.request.GET.get('sort')
        
        if sort_by == 'price_low':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'rating':
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating')
            ).order_by('-avg_rating')
        elif sort_by == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add current category to context if exists
        if hasattr(self, 'current_category'):
            context['current_category'] = self.current_category
            # Get subcategories for sidebar
            context['subcategories'] = self.current_category.children.filter(is_active=True)
            # Get breadcrumbs
            context['breadcrumbs'] = self.get_breadcrumbs()
        
        # Get all filter options from available products
        all_products = Product.objects.filter(is_active=True)
        
        # Get unique brands, colors, materials for filters
        context['brands'] = all_products.exclude(brand='').values_list('brand', flat=True).distinct()
        context['colors'] = all_products.exclude(color='').values_list('color', flat=True).distinct()
        context['materials'] = all_products.exclude(material='').values_list('material', flat=True).distinct()
        
        # Get price range
        price_range = all_products.aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        context['min_price'] = price_range['min_price'] or 0
        context['max_price'] = price_range['max_price'] or 1000
        
        # Get current filter values
        context['search_query'] = self.request.GET.get('q', '')
        context['current_min_price'] = self.request.GET.get('min_price', '')
        context['current_max_price'] = self.request.GET.get('max_price', '')
        context['current_brand'] = self.request.GET.get('brand', '')
        context['current_color'] = self.request.GET.get('color', '')
        context['current_material'] = self.request.GET.get('material', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        
        # Get all categories for navigation
        context['categories'] = Category.objects.filter(parent=None, is_active=True)
        
        return context
    
    def get_breadcrumbs(self):
        """Generate breadcrumb trail for current category"""
        breadcrumbs = []
        if hasattr(self, 'current_category'):
            category = self.current_category
            # Collect parent categories
            ancestors = []
            while category:
                ancestors.insert(0, category)
                category = category.parent
            
            # Build breadcrumbs
            for cat in ancestors:
                breadcrumbs.append({
                    'name': cat.name,
                    'slug': cat.slug,
                    'url': cat.get_absolute_url()
                })
        return breadcrumbs


class CategoryDetailView(ProductListView):
    """View for displaying products in a specific category with enhanced context"""
    
    def get_queryset(self):
        category_slug = self.kwargs.get('category_slug')
        self.current_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        
        # Get all products from this category and its subcategories
        products = self.current_category.get_products()
        
        # Apply search filter
        search_query = self.request.GET.get('q')
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(brand__icontains=search_query)
            )
        
        # Apply price range filters
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        
        if min_price:
            try:
                products = products.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                products = products.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        # Apply sorting
        sort_by = self.request.GET.get('sort')
        if sort_by == 'price_low':
            products = products.order_by('price')
        elif sort_by == 'price_high':
            products = products.order_by('-price')
        elif sort_by == 'newest':
            products = products.order_by('-created_at')
        elif sort_by == 'rating':
            products = products.annotate(
                avg_rating=Avg('reviews__rating')
            ).order_by('-avg_rating')
        
        return products
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add category specific context
        context['current_category'] = self.current_category
        context['subcategories'] = self.current_category.children.filter(is_active=True)
        context['breadcrumbs'] = self.get_breadcrumbs()
        
        # Get sibling categories for navigation
        if self.current_category.parent:
            context['sibling_categories'] = self.current_category.parent.children.filter(is_active=True).exclude(id=self.current_category.id)
            context['parent_category'] = self.current_category.parent
        else:
            context['sibling_categories'] = Category.objects.filter(parent=None, is_active=True).exclude(id=self.current_category.id)
        
        # Get category statistics
        context['total_products'] = self.get_queryset().count()
        
        # Get available filters for this category
        products_in_category = self.get_queryset()
        context['category_brands'] = products_in_category.exclude(brand='').values_list('brand', flat=True).distinct()
        context['category_colors'] = products_in_category.exclude(color='').values_list('color', flat=True).distinct()
        context['category_materials'] = products_in_category.exclude(material='').values_list('material', flat=True).distinct()
        
        # Get price range for this category
        price_range = products_in_category.aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        context['category_min_price'] = price_range['min_price'] or 0
        context['category_max_price'] = price_range['max_price'] or 1000
        
        return context
    
    def get_breadcrumbs(self):
        """Generate breadcrumb trail for current category"""
        breadcrumbs = []
        category = self.current_category
        ancestors = []
        
        # Collect all parent categories
        while category:
            ancestors.insert(0, category)
            category = category.parent
        
        # Build breadcrumbs
        for cat in ancestors:
            breadcrumbs.append({
                'name': cat.name,
                'slug': cat.slug,
                'url': cat.get_absolute_url(),
                'is_active': cat.id == self.current_category.id
            })
        
        return breadcrumbs


class ProductDetailView(DetailView):
    """Product detail page view"""
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    
    def get_object(self, queryset=None):
        """Get product by slug and category slug"""
        category_slug = self.kwargs.get('category_slug')
        product_slug = self.kwargs.get('product_slug')
        
        return get_object_or_404(
            Product,
            category__slug=category_slug,
            slug=product_slug,
            is_active=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Get related products from same category
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        # Get approved reviews
        context['reviews'] = product.reviews.filter(is_approved=True)
        
        # Calculate average rating
        avg_rating = product.reviews.filter(is_approved=True).aggregate(
            Avg('rating')
        )['rating__avg']
        context['avg_rating'] = round(avg_rating, 1) if avg_rating else 0
        
        # Get rating counts
        rating_counts = {}
        for i in range(1, 6):
            rating_counts[i] = product.reviews.filter(is_approved=True, rating=i).count()
        context['rating_counts'] = rating_counts
        
        # Check if user has already reviewed
        if self.request.user.is_authenticated:
            context['user_reviewed'] = product.reviews.filter(
                user=self.request.user
            ).exists()
        else:
            context['user_reviewed'] = False
        
        # Get all categories for navigation
        context['categories'] = Category.objects.filter(parent=None, is_active=True)
        
        # Get product images
        context['product_images'] = product.images.all()
        
        # Get product specifications
        context['specifications'] = {
            'Brand': product.brand or 'Not specified',
            'Material': product.material or 'Not specified',
            'Color': product.color or 'Not specified',
            'Dimensions': product.dimensions or 'Not specified',
            'Weight': f"{product.weight} kg" if product.weight else 'Not specified',
            'SKU': product.sku,
            'Category': product.category.name,
        }
        
        # Get breadcrumbs
        context['breadcrumbs'] = self.get_breadcrumbs(product)
        
        return context
    
    def get_breadcrumbs(self, product):
        """Generate breadcrumb trail for product"""
        breadcrumbs = []
        category = product.category
        ancestors = []
        
        # Collect all parent categories
        while category:
            ancestors.insert(0, category)
            category = category.parent
        
        # Add category breadcrumbs
        for cat in ancestors:
            breadcrumbs.append({
                'name': cat.name,
                'url': cat.get_absolute_url(),
                'is_active': False
            })
        
        # Add product breadcrumb
        breadcrumbs.append({
            'name': product.name,
            'url': None,
            'is_active': True
        })
        
        return breadcrumbs


@login_required
def add_review(request, product_id):
    """Add a review for a product"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Check if user already reviewed this product
        if product.reviews.filter(user=request.user).exists():
            messages.error(request, 'You have already reviewed this product.')
            return redirect('products:product_detail', 
                           category_slug=product.category.slug, 
                           product_slug=product.slug)
        
        # Create the review
        review = ProductReview.objects.create(
            product=product,
            user=request.user,
            rating=request.POST.get('rating'),
            title=request.POST.get('title'),
            comment=request.POST.get('comment')
        )
        
        messages.success(request, 'Your review has been submitted and is pending approval.')
        return redirect('products:product_detail', 
                       category_slug=product.category.slug, 
                       product_slug=product.slug)
    
    return redirect('products:product_list')


# ==================== API VIEWS ====================

class ProductViewSet(viewsets.ModelViewSet):
    """API view for products"""
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]  # Removed DjangoFilterBackend temporarily
    # filterset_class = ProductFilter  # Commented out
    search_fields = ['name', 'description', 'brand', 'sku']
    ordering_fields = ['price', 'created_at', 'name', 'stock_quantity']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        """Add a review to a product via API"""
        product = self.get_object()
        
        # Check if user already reviewed
        if product.reviews.filter(user=request.user).exists():
            return Response(
                {'error': 'You have already reviewed this product.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProductReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(product=product, user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for a product"""
        product = self.get_object()
        reviews = product.reviews.filter(is_approved=True)
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """Get related products"""
        product = self.get_object()
        related = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        serializer = self.get_serializer(related, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def by_category(self, request):
        """Get products by category slug"""
        category_slug = request.query_params.get('category')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            products = category.get_products()
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        return Response({'error': 'Category slug required'}, status=status.HTTP_400_BAD_REQUEST)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API view for categories (read-only)"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get all products in a category"""
        category = self.get_object()
        
        # Get products from category and subcategories
        if category.children.exists():
            child_categories = category.children.values_list('id', flat=True)
            category_ids = list(child_categories) + [category.id]
            products = Product.objects.filter(category_id__in=category_ids, is_active=True)
        else:
            products = Product.objects.filter(category=category, is_active=True)
        
        # Apply pagination
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def subcategories(self, request, pk=None):
        """Get subcategories of a category"""
        category = self.get_object()
        subcategories = category.children.filter(is_active=True)
        serializer = self.get_serializer(subcategories, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get full category tree"""
        root_categories = Category.objects.filter(parent=None, is_active=True)
        serializer = self.get_serializer(root_categories, many=True)
        return Response(serializer.data)