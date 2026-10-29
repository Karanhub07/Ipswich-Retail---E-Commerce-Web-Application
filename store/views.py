from django.shortcuts import get_object_or_404, render
from .models import Category, Product


def product_list(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    products = Product.objects.select_related('category').all()

    if query:
        products = products.filter(name__icontains=query)
    if category_slug:
        products = products.filter(category__slug=category_slug)

    categories = Category.objects.all()
    return render(request, 'store/product_list.html', {
        'products': products,
        'query': query,
        'categories': categories,
        'selected_category': category_slug,
    })


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    return render(request, 'store/product_detail.html', {'product': product})
