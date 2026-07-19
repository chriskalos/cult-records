from dataclasses import dataclass
from decimal import Decimal

from home.models import Product


CART_SESSION_KEY = "cart"
MAX_ITEM_QUANTITY = 99


@dataclass(frozen=True)
class CartLine:
    product: Product
    quantity: int

    @property
    def total_price(self):
        return self.product.price * self.quantity


class Cart:
    def __init__(self, session):
        self.session = session
        stored_cart = session.get(CART_SESSION_KEY, {})
        self._quantities = (
            {
                str(product_id): quantity
                for product_id, quantity in stored_cart.items()
                if isinstance(quantity, int)
                and 1 <= quantity <= MAX_ITEM_QUANTITY
            }
            if isinstance(stored_cart, dict)
            else {}
        )
        if self._quantities != stored_cart:
            self._save()

    def add(self, product, quantity=1):
        product_id = str(product.pk)
        new_quantity = self._quantities.get(product_id, 0) + quantity
        if new_quantity > MAX_ITEM_QUANTITY:
            raise ValueError(
                f"A cart can contain at most {MAX_ITEM_QUANTITY} of one product."
            )
        self._quantities[product_id] = new_quantity
        self._save()

    def update(self, product, quantity):
        self._quantities[str(product.pk)] = quantity
        self._save()

    def remove(self, product_id):
        if self._quantities.pop(str(product_id), None) is not None:
            self._save()

    def clear(self):
        self._quantities.clear()
        self._save()

    @property
    def lines(self):
        products = Product.objects.public().filter(pk__in=self._quantities)
        products_by_id = {str(product.pk): product for product in products}
        available_quantities = {
            product_id: quantity
            for product_id, quantity in self._quantities.items()
            if product_id in products_by_id
            and isinstance(quantity, int)
            and 1 <= quantity <= MAX_ITEM_QUANTITY
        }

        if available_quantities != self._quantities:
            self._quantities = available_quantities
            self._save()

        return [
            CartLine(products_by_id[product_id], quantity)
            for product_id, quantity in self._quantities.items()
        ]

    @property
    def quantity(self):
        return sum(self._quantities.values())

    @property
    def subtotal(self):
        return sum(
            (line.total_price for line in self.lines),
            start=Decimal("0.00"),
        )

    def _save(self):
        self.session[CART_SESSION_KEY] = self._quantities
        self.session.modified = True
