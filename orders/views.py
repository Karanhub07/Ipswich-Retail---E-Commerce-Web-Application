from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from store.models import Product
from .forms import CheckoutForm
from .models import Order, OrderItem


@login_required(login_url='orders:login')
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, 'Your cart is empty.')
        return redirect('store:product_list')

    products = list(Product.objects.filter(id__in=cart.keys()))
    items = []
    total = 0
    for product in products:
        qty = cart.get(str(product.id), 0)
        subtotal = product.price * qty
        total += subtotal
        items.append({'product': product, 'quantity': qty, 'subtotal': subtotal})

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Stock validation before committing order
                for item in items:
                    prod = Product.objects.select_for_update().get(id=item['product'].id)
                    if prod.stock < item['quantity']:
                        messages.error(request, f'Sorry, {prod.name} only has {prod.stock} units left.')
                        return redirect('cart:cart_detail')

                order = form.save(commit=False)
                order.user = request.user
                order.total = total
                order.save()

                for item in items:
                    prod = Product.objects.get(id=item['product'].id)
                    OrderItem.objects.create(
                        order=order,
                        product=prod,
                        quantity=item['quantity'],
                        price=prod.price,
                    )
                    prod.stock -= item['quantity']
                    prod.save()

                request.session['cart'] = {}
                request.session.modified = True
                messages.success(request, f'Order #{order.id} placed successfully!')
                return redirect('orders:order_success', order_id=order.id)
    else:
        form = CheckoutForm()

    return render(request, 'orders/checkout.html', {'form': form, 'items': items, 'total': total})


@login_required(login_url='orders:login')
def order_success(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})


@login_required(login_url='orders:login')
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})


def register(request):
    if request.user.is_authenticated:
        return redirect('store:product_list')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Ipswich Retail, {user.username}!')
            return redirect('store:product_list')
    else:
        form = UserCreationForm()
    return render(request, 'orders/register.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('store:product_list')
