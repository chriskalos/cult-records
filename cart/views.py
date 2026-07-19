from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from home.models import Product

from .cart import Cart
from .forms import CartQuantityForm


def detail(request):
    cart = Cart(request.session)
    return render(
        request,
        "cart/detail.html",
        {
            "cart": cart,
            "cart_lines": cart.lines,
        },
    )


@require_POST
def add(request, product_id):
    product = get_object_or_404(Product.objects.public(), pk=product_id)
    form = CartQuantityForm(request.POST)
    cart = Cart(request.session)

    if form.is_valid():
        try:
            cart.add(product, form.cleaned_data["quantity"])
        except ValueError as error:
            messages.error(request, str(error))
        else:
            messages.success(request, f"{product.title} was added to your cart.")
    else:
        messages.error(request, "Choose a quantity between 1 and 99.")

    return redirect(_return_url(request, product.get_absolute_url()))


@require_POST
def update(request, product_id):
    product = get_object_or_404(Product.objects.public(), pk=product_id)
    form = CartQuantityForm(request.POST)

    if form.is_valid():
        Cart(request.session).update(product, form.cleaned_data["quantity"])
        messages.success(request, f"The quantity for {product.title} was updated.")
    else:
        messages.error(request, "Choose a quantity between 1 and 99.")

    return redirect("cart:detail")


@require_POST
def remove(request, product_id):
    product = Product.objects.public().filter(pk=product_id).first()
    Cart(request.session).remove(product_id)
    if product:
        messages.success(request, f"{product.title} was removed from your cart.")
    return redirect("cart:detail")


def _return_url(request, fallback):
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback or reverse("cart:detail")
