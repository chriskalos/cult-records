import stripe
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from home.models import Product

from .cart import Cart
from .checkout import (
    PAID_CHECKOUT_EVENTS,
    confirm_paid_order,
    create_order,
    create_stripe_checkout_session,
    expire_order,
    has_stripe_test_key,
)
from .forms import CartQuantityForm
from .models import Order


PENDING_ORDERS_SESSION_KEY = "pending_checkout_orders"


def detail(request):
    cart = Cart(request.session)
    return render(
        request,
        "cart/detail.html",
        {
            "cart": cart,
            "cart_lines": cart.lines,
            "checkout_ready": has_stripe_test_key(),
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


@require_POST
def checkout_start(request):
    cart = Cart(request.session)
    if not cart.lines:
        messages.error(request, "Add at least one product before checkout.")
        return redirect("cart:detail")
    if not has_stripe_test_key():
        messages.error(request, "Checkout is currently unavailable.")
        return redirect("cart:detail")

    order = create_order(cart, request.user)
    try:
        checkout_session = create_stripe_checkout_session(request, order)
    except stripe.StripeError:
        order.delete()
        messages.error(
            request,
            "Checkout could not be started. Please try again.",
        )
        return redirect("cart:detail")

    pending_orders = request.session.get(PENDING_ORDERS_SESSION_KEY, [])
    pending_orders.append(str(order.pk))
    request.session[PENDING_ORDERS_SESSION_KEY] = pending_orders[-10:]

    response = HttpResponseRedirect(checkout_session.url)
    response.status_code = 303
    return response


def checkout_success(request):
    session_id = request.GET.get("session_id", "")
    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        stripe_checkout_session_id=session_id,
    )

    if order.status != Order.Status.PAID and has_stripe_test_key():
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            checkout_session = stripe.checkout.Session.retrieve(session_id)
        except stripe.StripeError:
            return render(
                request,
                "cart/checkout_success.html",
                {"order": order, "confirmation_unavailable": True},
                status=503,
            )
        confirmed_order = confirm_paid_order(checkout_session)
        if confirmed_order:
            order = confirmed_order

    pending_orders = request.session.get(PENDING_ORDERS_SESSION_KEY, [])
    if order.status == Order.Status.PAID and str(order.pk) in pending_orders:
        Cart(request.session).remove_purchased_quantities(
            {item.product_code: item.quantity for item in order.items.all()}
        )
        request.session[PENDING_ORDERS_SESSION_KEY] = [
            order_id for order_id in pending_orders if order_id != str(order.pk)
        ]

    return render(request, "cart/checkout_success.html", {"order": order})


def checkout_cancel(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    return render(request, "cart/checkout_cancel.html", {"order": order})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse(status=503)

    stripe.api_key = settings.STRIPE_SECRET_KEY
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            request.headers.get("Stripe-Signature", ""),
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)

    event_type = event["type"]
    checkout_session = event["data"]["object"]
    if event_type in PAID_CHECKOUT_EVENTS:
        confirm_paid_order(checkout_session)
    elif event_type == "checkout.session.expired":
        expire_order(checkout_session)

    return HttpResponse(status=200)


def _return_url(request, fallback):
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return fallback or reverse("cart:detail")
