from .cart import Cart


def cart_summary(request):
    cart = Cart(request.session)
    if cart.quantity:
        _ = cart.lines
    return {"cart_item_count": cart.quantity}
