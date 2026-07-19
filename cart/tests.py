from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from home.models import Product

from .cart import CART_SESSION_KEY


class CartTests(TestCase):
    def setUp(self):
        self.album = Product.objects.create(
            product_id="CARTALBUMLP",
            artist="Cart Artist",
            title="Cart Album",
            description="A cart test album.",
            product_type=Product.ProductType.LP,
            price=Decimal("12.50"),
        )
        self.cd = Product.objects.create(
            product_id="CARTSINGLECD",
            artist="Cart Artist",
            title="Cart Single",
            description="A second cart test product.",
            product_type=Product.ProductType.CD,
            price=Decimal("4.25"),
        )

    def test_multiple_products_and_quantities_can_be_added(self):
        self.client.post(
            reverse("cart:add", args=[self.album.pk]),
            {"quantity": 2},
        )
        self.client.post(
            reverse("cart:add", args=[self.cd.pk]),
            {"quantity": 3},
        )
        self.client.post(
            reverse("cart:add", args=[self.album.pk]),
            {"quantity": 1},
        )

        self.assertEqual(
            self.client.session[CART_SESSION_KEY],
            {self.album.pk: 3, self.cd.pk: 3},
        )

    def test_cart_page_displays_lines_quantities_and_subtotal(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {self.album.pk: 2, self.cd.pk: 1}
        session.save()

        response = self.client.get(reverse("cart:detail"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "cart/detail.html")
        self.assertContains(response, "Cart Album")
        self.assertContains(response, "Cart Single")
        self.assertContains(response, 'value="2"')
        self.assertContains(response, "29.25€")
        self.assertContains(response, "Subtotal (3 items)")

    def test_item_quantity_can_be_updated(self):
        self.client.post(
            reverse("cart:add", args=[self.album.pk]),
            {"quantity": 1},
        )

        response = self.client.post(
            reverse("cart:update", args=[self.album.pk]),
            {"quantity": 7},
        )

        self.assertRedirects(response, reverse("cart:detail"))
        self.assertEqual(self.client.session[CART_SESSION_KEY][self.album.pk], 7)

    def test_item_can_be_removed(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {self.album.pk: 1, self.cd.pk: 2}
        session.save()

        response = self.client.post(reverse("cart:remove", args=[self.album.pk]))

        self.assertRedirects(response, reverse("cart:detail"))
        self.assertEqual(
            self.client.session[CART_SESSION_KEY],
            {self.cd.pk: 2},
        )

    def test_invalid_quantity_does_not_change_the_cart(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {self.album.pk: 2}
        session.save()

        self.client.post(
            reverse("cart:update", args=[self.album.pk]),
            {"quantity": 0},
        )

        self.assertEqual(self.client.session[CART_SESSION_KEY][self.album.pk], 2)

    def test_quantity_cannot_exceed_cart_limit_when_adding(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {self.album.pk: 98}
        session.save()

        self.client.post(
            reverse("cart:add", args=[self.album.pk]),
            {"quantity": 2},
        )

        self.assertEqual(self.client.session[CART_SESSION_KEY][self.album.pk], 98)

    def test_hidden_products_cannot_be_added(self):
        self.album.is_visible = False
        self.album.save(update_fields=("is_visible",))

        response = self.client.post(
            reverse("cart:add", args=[self.album.pk]),
            {"quantity": 1},
        )

        self.assertEqual(response.status_code, 404)
        self.assertNotIn(CART_SESSION_KEY, self.client.session)

    def test_product_that_becomes_hidden_is_removed_from_cart(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {self.album.pk: 2}
        session.save()
        self.album.is_visible = False
        self.album.save(update_fields=("is_visible",))

        response = self.client.get(reverse("cart:detail"))

        self.assertContains(response, "Your cart is empty")
        self.assertEqual(self.client.session[CART_SESSION_KEY], {})

    def test_cart_mutations_require_post(self):
        urls = (
            reverse("cart:add", args=[self.album.pk]),
            reverse("cart:update", args=[self.album.pk]),
            reverse("cart:remove", args=[self.album.pk]),
        )

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 405)

    def test_external_next_url_is_not_used_after_add(self):
        response = self.client.post(
            reverse("cart:add", args=[self.album.pk]),
            {"quantity": 1, "next": "https://example.com/steal-session"},
        )

        self.assertRedirects(response, self.album.get_absolute_url())

    def test_header_reports_total_cart_quantity(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {self.album.pk: 2, self.cd.pk: 3}
        session.save()

        response = self.client.get(reverse("home"))

        self.assertContains(response, 'aria-hidden="true">(5)</span>')
        self.assertContains(response, "with 5 items")

    def test_product_page_has_working_add_to_cart_form(self):
        response = self.client.get(self.album.get_absolute_url())

        self.assertContains(
            response,
            f'action="{reverse("cart:add", args=[self.album.pk])}"',
        )
        self.assertContains(response, 'name="quantity"')
        self.assertContains(response, 'type="submit" class="btn btn-primary">Add to cart')
