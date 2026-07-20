from decimal import Decimal

import stripe
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from ham.services import grant_enlightenment_for_order

from .models import Order, OrderItem


PAID_CHECKOUT_EVENTS = {
    "checkout.session.completed",
    "checkout.session.async_payment_succeeded",
}


def has_stripe_test_key():
    key = settings.STRIPE_SECRET_KEY
    return bool(key) and key.startswith(("sk_test_", "rk_test_"))


@transaction.atomic
def create_order(cart, user):
    if not user.is_authenticated:
        raise PermissionDenied("Authentication is required to create an order.")

    lines = cart.lines
    order = Order.objects.create(
        user=user,
        currency=settings.STRIPE_CURRENCY,
        subtotal=sum(
            (line.total_price for line in lines),
            start=Decimal("0.00"),
        ),
    )
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                product=line.product,
                product_code=line.product.product_id,
                artist=line.product.artist,
                title=line.product.title,
                product_type=line.product.product_type,
                unit_price=line.product.price,
                quantity=line.quantity,
            )
            for line in lines
        ]
    )
    return order


def create_stripe_checkout_session(request, order):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    success_url = request.build_absolute_uri(reverse("cart:checkout_success"))
    success_url = f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = request.build_absolute_uri(
        reverse("cart:checkout_cancel", args=[order.pk])
    )
    parameters = {
        "mode": "payment",
        "payment_method_types": ["card"],
        "line_items": [
            {
                "price_data": {
                    "currency": order.currency,
                    "unit_amount": _minor_units(item.unit_price),
                    "product_data": {
                        "name": item.title,
                        "description": f"{item.artist} · {item.get_product_type_display()}",
                    },
                },
                "quantity": item.quantity,
            }
            for item in order.items.all()
        ],
        "success_url": success_url,
        "cancel_url": cancel_url,
        "client_reference_id": str(order.pk),
        "metadata": {"order_id": str(order.pk)},
    }
    if order.user and order.user.email:
        parameters["customer_email"] = order.user.email

    checkout_session = stripe.checkout.Session.create(**parameters)
    order.stripe_checkout_session_id = checkout_session.id
    order.save(update_fields=("stripe_checkout_session_id",))
    return checkout_session


@transaction.atomic
def confirm_paid_order(checkout_session):
    if _value(checkout_session, "payment_status") != "paid":
        return None

    metadata = _value(checkout_session, "metadata", {})
    order_id = _value(metadata, "order_id")
    session_id = _value(checkout_session, "id")
    if not order_id or not session_id:
        return None

    try:
        order = Order.objects.select_for_update().get(pk=order_id)
    except (Order.DoesNotExist, ValueError):
        return None

    if (
        order.stripe_checkout_session_id
        and order.stripe_checkout_session_id != session_id
    ):
        return None
    if _value(checkout_session, "currency", "").lower() != order.currency:
        return None
    if _value(checkout_session, "amount_total") != _minor_units(order.subtotal):
        return None

    if order.status != Order.Status.PAID:
        customer_details = _value(checkout_session, "customer_details", {})
        payment_intent = _value(checkout_session, "payment_intent", "")
        if not isinstance(payment_intent, str):
            payment_intent = _value(payment_intent, "id", "")

        order.status = Order.Status.PAID
        order.stripe_checkout_session_id = session_id
        order.stripe_payment_intent_id = payment_intent or ""
        order.customer_email = _value(customer_details, "email", "") or ""
        order.paid_at = timezone.now()
        order.save(
            update_fields=(
                "status",
                "stripe_checkout_session_id",
                "stripe_payment_intent_id",
                "customer_email",
                "paid_at",
            )
        )

    grant_enlightenment_for_order(order)
    return order


@transaction.atomic
def expire_order(checkout_session):
    metadata = _value(checkout_session, "metadata", {})
    order_id = _value(metadata, "order_id")
    session_id = _value(checkout_session, "id")
    if not order_id or not session_id:
        return

    Order.objects.filter(
        pk=order_id,
        status=Order.Status.PENDING,
        stripe_checkout_session_id=session_id,
    ).update(status=Order.Status.EXPIRED)


def _minor_units(amount):
    return int(amount * 100)


def _value(value, key, default=None):
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)
