from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from store.models import Product


def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total = 0
    if cart:
        products = Product.objects.filter(id__in=cart.keys())
        for product in products:
            qty = cart.get(str(product.id), 0)
            subtotal = product.price * qty
            total += subtotal
            cart_items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})
    return render(request, 'cart/cart_detail.html', {'cart_items': cart_items, 'total': total})


def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    if product.stock <= 0:
        messages.error(request, f'{product.name} is out of stock.')
        return redirect('store:product_detail', pk=product.id)

    qty = int(request.POST.get('quantity', 1))
    cart = request.session.setdefault('cart', {})
    current_qty = cart.get(str(product.id), 0)

    if current_qty + qty > product.stock:
        messages.error(request, f'Cannot add {qty} more. Only {product.stock} items available in stock.')
    else:
        cart[str(product.id)] = current_qty + qty
        request.session.modified = True
        messages.success(request, f'Added {product.name} to your cart.')

    return redirect('cart:cart_detail')


def cart_update(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = request.session.get('cart', {})
    if str(product.id) in cart:
        try:
            qty = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            qty = 1

        if qty <= 0:
            del cart[str(product.id)]
            messages.info(request, f'Removed {product.name} from your cart.')
        elif qty > product.stock:
            messages.error(request, f'Only {product.stock} units available in stock.')
        else:
            cart[str(product.id)] = qty
            messages.success(request, f'Updated quantity for {product.name}.')
        request.session.modified = True

    return redirect('cart:cart_detail')


def cart_remove(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = request.session.get('cart', {})
    if str(product.id) in cart:
        del cart[str(product.id)]
        request.session.modified = True
        messages.info(request, f'Removed {product.name} from your cart.')
    return redirect('cart:cart_detail')
