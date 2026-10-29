def cart_context(request):
    cart = request.session.get('cart', {})
    total_items = sum(cart.values()) if isinstance(cart, dict) else 0
    return {'cart_total_items': total_items}
