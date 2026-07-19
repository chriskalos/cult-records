from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import HamClearance


ENLIGHTENMENT_PRODUCT_CODE = "CLXYZCD"
ENLIGHTENMENT_QUANTITY = 42


def order_qualifies_for_enlightenment(order):
    return bool(
        order.user_id
        and order.status == "paid"
        and order.items.filter(
            product_code=ENLIGHTENMENT_PRODUCT_CODE,
            quantity=ENLIGHTENMENT_QUANTITY,
        ).exists()
    )


@transaction.atomic
def grant_enlightenment_for_order(order):
    if not order_qualifies_for_enlightenment(order):
        return None

    user = get_user_model().objects.select_for_update().get(pk=order.user_id)
    clearance, _ = HamClearance.objects.get_or_create(user=user)
    if clearance.is_enlightened:
        return clearance

    clearance.is_enlightened = True
    clearance.enlightened_at = timezone.now()
    clearance.source_order = order
    clearance.save(
        update_fields=("is_enlightened", "enlightened_at", "source_order")
    )
    return clearance


def user_has_ham_access(user):
    return bool(
        user.is_authenticated
        and HamClearance.objects.filter(
            user=user,
            is_enlightened=True,
        ).exists()
    )
