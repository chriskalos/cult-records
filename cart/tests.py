from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import stripe
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse

from home.models import Product

from .cart import CART_SESSION_KEY
from .models import Order, OrderItem
from .views import PENDING_ORDERS_SESSION_KEY


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

    def test_header_count_prunes_product_that_becomes_hidden(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {self.album.pk: 2}
        session.save()
        self.album.is_visible = False
        self.album.save(update_fields=("is_visible",))

        response = self.client.get(reverse("home"))

        self.assertContains(response, 'aria-hidden="true">(0)</span>')
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


class CheckoutTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="checkout-user",
            email="checkout@example.com",
            password="test-password",
        )
        self.client.force_login(self.user)
        self.album = Product.objects.create(
            product_id="CHECKOUTLP",
            artist="Checkout Artist",
            title="Checkout Album",
            description="A checkout test album.",
            product_type=Product.ProductType.LP,
            price=Decimal("12.50"),
        )
        self.cd = Product.objects.create(
            product_id="CHECKOUTCD",
            artist="Checkout Artist",
            title="Checkout CD",
            description="A checkout test CD.",
            product_type=Product.ProductType.CD,
            price=Decimal("4.25"),
        )

    def _put_products_in_cart(self):
        session = self.client.session
        session[CART_SESSION_KEY] = {self.album.pk: 2, self.cd.pk: 1}
        session.save()

    def _create_pending_order(self):
        order = Order.objects.create(
            user=self.user,
            currency="eur",
            subtotal=Decimal("25.00"),
            stripe_checkout_session_id="cs_test_confirmed",
        )
        OrderItem.objects.create(
            order=order,
            product=self.album,
            product_code=self.album.pk,
            artist=self.album.artist,
            title=self.album.title,
            product_type=self.album.product_type,
            unit_price=self.album.price,
            quantity=2,
        )
        return order

    def _paid_checkout_session(self, order):
        return {
            "id": order.stripe_checkout_session_id,
            "payment_status": "paid",
            "payment_intent": "pi_test_123",
            "currency": "eur",
            "amount_total": 2500,
            "metadata": {"order_id": str(order.pk)},
            "customer_details": {"email": "buyer@example.com"},
        }

    def test_empty_cart_cannot_start_checkout(self):
        with patch("cart.checkout.stripe.checkout.Session.create") as create_session:
            response = self.client.post(reverse("cart:checkout_start"))

        self.assertRedirects(response, reverse("cart:detail"))
        create_session.assert_not_called()
        self.assertFalse(Order.objects.exists())

    @override_settings(STRIPE_SECRET_KEY="sk_test_example")
    def test_anonymous_user_cannot_start_checkout(self):
        self.client.logout()
        self._put_products_in_cart()

        with patch("cart.checkout.stripe.checkout.Session.create") as create_session:
            response = self.client.post(reverse("cart:checkout_start"))

        login_url = reverse("accounts:login")
        checkout_url = reverse("cart:checkout_start")
        self.assertRedirects(response, f"{login_url}?next={checkout_url}")
        create_session.assert_not_called()
        self.assertFalse(Order.objects.exists())

    @override_settings(STRIPE_SECRET_KEY="sk_test_example")
    def test_anonymous_cart_prompts_user_to_sign_in_for_checkout(self):
        self.client.logout()
        self._put_products_in_cart()

        response = self.client.get(reverse("cart:detail"))

        self.assertContains(response, "Sign in to checkout")
        self.assertNotContains(response, 'action="/cart/checkout/"')

    def test_user_cannot_view_another_users_checkout(self):
        order = self._create_pending_order()
        other_user = get_user_model().objects.create_user(
            username="other-checkout-user",
            password="test-password",
        )
        self.client.force_login(other_user)

        success_response = self.client.get(
            reverse("cart:checkout_success"),
            {"session_id": order.stripe_checkout_session_id},
        )
        cancel_response = self.client.get(
            reverse("cart:checkout_cancel", args=[order.pk])
        )

        self.assertEqual(success_response.status_code, 404)
        self.assertEqual(cancel_response.status_code, 404)

    @override_settings(STRIPE_SECRET_KEY="")
    def test_missing_stripe_key_prevents_checkout(self):
        self._put_products_in_cart()

        with patch("cart.checkout.stripe.checkout.Session.create") as create_session:
            response = self.client.post(reverse("cart:checkout_start"))

        self.assertRedirects(response, reverse("cart:detail"))
        create_session.assert_not_called()
        self.assertFalse(Order.objects.exists())

    @override_settings(STRIPE_SECRET_KEY="sk_live_not_allowed")
    def test_live_stripe_key_is_rejected(self):
        self._put_products_in_cart()

        with patch("cart.checkout.stripe.checkout.Session.create") as create_session:
            response = self.client.post(reverse("cart:checkout_start"))

        self.assertRedirects(response, reverse("cart:detail"))
        create_session.assert_not_called()
        self.assertFalse(Order.objects.exists())

    @override_settings(STRIPE_SECRET_KEY="sk_test_example", STRIPE_CURRENCY="eur")
    @patch("cart.checkout.stripe.checkout.Session.create")
    def test_checkout_snapshots_cart_and_redirects_to_stripe(self, create_session):
        self._put_products_in_cart()
        create_session.return_value = SimpleNamespace(
            id="cs_test_created",
            url="https://checkout.stripe.com/c/pay/cs_test_created",
        )

        response = self.client.post(reverse("cart:checkout_start"))

        self.assertEqual(response.status_code, 303)
        self.assertEqual(response["Location"], create_session.return_value.url)
        order = Order.objects.get()
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.subtotal, Decimal("29.25"))
        self.assertEqual(order.stripe_checkout_session_id, "cs_test_created")
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(
            self.client.session[PENDING_ORDERS_SESSION_KEY],
            [str(order.pk)],
        )

        parameters = create_session.call_args.kwargs
        self.assertEqual(parameters["mode"], "payment")
        self.assertEqual(parameters["payment_method_types"], ["card"])
        self.assertEqual(parameters["customer_email"], "checkout@example.com")
        self.assertEqual(parameters["metadata"], {"order_id": str(order.pk)})
        self.assertEqual(parameters["line_items"][0]["price_data"]["unit_amount"], 1250)
        self.assertEqual(parameters["line_items"][0]["quantity"], 2)
        self.assertIn("{CHECKOUT_SESSION_ID}", parameters["success_url"])

    @override_settings(STRIPE_SECRET_KEY="sk_test_example")
    @patch("cart.checkout.stripe.checkout.Session.create")
    def test_stripe_error_keeps_cart_and_discards_pending_order(self, create_session):
        self._put_products_in_cart()
        create_session.side_effect = stripe.StripeError("Stripe is unavailable")

        response = self.client.post(reverse("cart:checkout_start"))

        self.assertRedirects(response, reverse("cart:detail"))
        self.assertFalse(Order.objects.exists())
        self.assertEqual(
            self.client.session[CART_SESSION_KEY],
            {self.album.pk: 2, self.cd.pk: 1},
        )

    @override_settings(STRIPE_SECRET_KEY="sk_test_example")
    @patch("cart.views.stripe.checkout.Session.retrieve")
    def test_success_page_confirms_payment_and_removes_purchased_units(
        self,
        retrieve_session,
    ):
        order = self._create_pending_order()
        retrieve_session.return_value = self._paid_checkout_session(order)
        session = self.client.session
        session[CART_SESSION_KEY] = {self.album.pk: 4, self.cd.pk: 1}
        session[PENDING_ORDERS_SESSION_KEY] = [str(order.pk)]
        session.save()

        response = self.client.get(
            reverse("cart:checkout_success"),
            {"session_id": order.stripe_checkout_session_id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Payment confirmed")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.stripe_payment_intent_id, "pi_test_123")
        self.assertEqual(order.customer_email, "buyer@example.com")
        self.assertIsNotNone(order.paid_at)
        self.assertEqual(
            self.client.session[CART_SESSION_KEY],
            {self.album.pk: 2, self.cd.pk: 1},
        )
        self.assertEqual(self.client.session[PENDING_ORDERS_SESSION_KEY], [])

        self.client.get(
            reverse("cart:checkout_success"),
            {"session_id": order.stripe_checkout_session_id},
        )
        self.assertEqual(
            self.client.session[CART_SESSION_KEY],
            {self.album.pk: 2, self.cd.pk: 1},
        )

    @override_settings(STRIPE_SECRET_KEY="sk_test_example")
    @patch("cart.views.stripe.checkout.Session.retrieve")
    def test_unpaid_checkout_does_not_clear_cart(self, retrieve_session):
        order = self._create_pending_order()
        checkout_session = self._paid_checkout_session(order)
        checkout_session["payment_status"] = "unpaid"
        retrieve_session.return_value = checkout_session
        session = self.client.session
        session[CART_SESSION_KEY] = {self.album.pk: 2}
        session[PENDING_ORDERS_SESSION_KEY] = [str(order.pk)]
        session.save()

        response = self.client.get(
            reverse("cart:checkout_success"),
            {"session_id": order.stripe_checkout_session_id},
        )

        self.assertContains(response, "Confirmation pending")
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(self.client.session[CART_SESSION_KEY], {self.album.pk: 2})

    def test_checkout_cancel_page_keeps_cart(self):
        order = self._create_pending_order()
        self._put_products_in_cart()

        response = self.client.get(
            reverse("cart:checkout_cancel", args=[order.pk])
        )

        self.assertContains(response, "Checkout cancelled")
        self.assertEqual(
            self.client.session[CART_SESSION_KEY],
            {self.album.pk: 2, self.cd.pk: 1},
        )

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example",
        STRIPE_WEBHOOK_SECRET="whsec_example",
    )
    @patch("cart.views.stripe.Webhook.construct_event")
    def test_signed_webhook_marks_order_paid(self, construct_event):
        order = self._create_pending_order()
        construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": self._paid_checkout_session(order)},
        }

        response = self.client.post(
            reverse("cart:stripe_webhook"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="test-signature",
        )

        self.assertEqual(response.status_code, 200)
        construct_event.assert_called_once_with(
            b"{}",
            "test-signature",
            "whsec_example",
        )
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)

    @override_settings(STRIPE_WEBHOOK_SECRET="whsec_example")
    @patch("cart.views.stripe.Webhook.construct_event", side_effect=ValueError)
    def test_invalid_webhook_is_rejected(self, construct_event):
        response = self.client.post(
            reverse("cart:stripe_webhook"),
            data=b"not-json",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="invalid",
        )

        self.assertEqual(response.status_code, 400)

    @override_settings(STRIPE_WEBHOOK_SECRET="")
    def test_unconfigured_webhook_is_unavailable(self):
        response = self.client.post(
            reverse("cart:stripe_webhook"),
            data=b"{}",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 503)


class OrderModelTests(TestCase):
    def test_order_item_keeps_product_snapshot_after_product_deletion(self):
        product = Product.objects.create(
            product_id="SNAPSHOTCD",
            artist="Original Artist",
            title="Original Title",
            description="An order snapshot test.",
            product_type=Product.ProductType.CD,
            price=Decimal("7.50"),
        )
        order = Order.objects.create(currency="eur", subtotal=Decimal("15.00"))
        item = OrderItem.objects.create(
            order=order,
            product=product,
            product_code=product.pk,
            artist=product.artist,
            title=product.title,
            product_type=product.product_type,
            unit_price=product.price,
            quantity=2,
        )

        product.delete()
        item.refresh_from_db()

        self.assertIsNone(item.product)
        self.assertEqual(item.product_code, "SNAPSHOTCD")
        self.assertEqual(item.artist, "Original Artist")
        self.assertEqual(item.title, "Original Title")
        self.assertEqual(item.total_price, Decimal("15.00"))
