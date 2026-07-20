from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from cart.checkout import confirm_paid_order
from cart.models import Order, OrderItem
from home.models import Product

from .models import ArchiveDocument, Directive, HamClearance, HumanAsset
from .services import grant_enlightenment_for_order


class EnlightenmentTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="network-member",
            password="correct-horse-battery-staple",
        )
        self.target = Product.objects.get(product_id="CLXYZCD")
        self.other_product = Product.objects.create(
            product_id="ORDINARYCD",
            artist="Ordinary Artist",
            title="Ordinary Album",
            description="Nothing to report.",
            product_type=Product.ProductType.CD,
            price=Decimal("5.00"),
        )

    def make_order(self, *, quantity=42, user=True, status=Order.Status.PENDING):
        subtotal = self.target.price * quantity
        order = Order.objects.create(
            user=self.user if user else None,
            status=status,
            currency="eur",
            subtotal=subtotal,
            stripe_checkout_session_id=f"cs_{quantity}_{Order.objects.count()}",
        )
        OrderItem.objects.create(
            order=order,
            product=self.target,
            product_code=self.target.pk,
            artist=self.target.artist,
            title=self.target.title,
            product_type=self.target.product_type,
            unit_price=self.target.price,
            quantity=quantity,
        )
        return order

    def paid_session(self, order):
        return {
            "id": order.stripe_checkout_session_id,
            "payment_status": "paid",
            "payment_intent": "pi_enlightened",
            "currency": "eur",
            "amount_total": int(order.subtotal * 100),
            "metadata": {"order_id": str(order.pk)},
            "customer_details": {"email": "member@example.com"},
        }

    def test_accounts_have_no_enlightenment_by_default(self):
        self.assertFalse(HamClearance.objects.filter(user=self.user).exists())

    def test_verified_order_of_exactly_42_grants_enlightenment(self):
        order = self.make_order()

        confirm_paid_order(self.paid_session(order))

        clearance = HamClearance.objects.get(user=self.user)
        self.assertTrue(clearance.is_enlightened)
        self.assertEqual(clearance.source_order, order)
        self.assertIsNotNone(clearance.enlightened_at)

    def test_other_items_can_share_the_qualifying_order(self):
        order = self.make_order()
        OrderItem.objects.create(
            order=order,
            product=self.other_product,
            product_code=self.other_product.pk,
            artist=self.other_product.artist,
            title=self.other_product.title,
            product_type=self.other_product.product_type,
            unit_price=self.other_product.price,
            quantity=1,
        )
        order.subtotal += self.other_product.price
        order.save(update_fields=("subtotal",))

        confirm_paid_order(self.paid_session(order))

        self.assertTrue(HamClearance.objects.get(user=self.user).is_enlightened)

    def test_quantity_must_be_exact_and_cannot_accumulate(self):
        for quantity in (21, 41, 43):
            order = self.make_order(quantity=quantity, status=Order.Status.PAID)
            self.assertIsNone(grant_enlightenment_for_order(order))

        self.assertFalse(HamClearance.objects.filter(user=self.user).exists())

    def test_anonymous_order_does_not_grant_account_access(self):
        order = self.make_order(user=False, status=Order.Status.PAID)

        self.assertIsNone(grant_enlightenment_for_order(order))
        self.assertFalse(HamClearance.objects.exists())

    def test_repeated_confirmation_keeps_original_clearance(self):
        first_order = self.make_order()
        confirm_paid_order(self.paid_session(first_order))
        first_granted_at = HamClearance.objects.get(user=self.user).enlightened_at

        second_order = self.make_order()
        confirm_paid_order(self.paid_session(second_order))

        clearance = HamClearance.objects.get(user=self.user)
        self.assertEqual(clearance.source_order, first_order)
        self.assertEqual(clearance.enlightened_at, first_granted_at)


class NetworkSeedTests(TestCase):
    def test_initial_network_has_complete_cloudinary_dossiers(self):
        assets = HumanAsset.objects.all()

        self.assertEqual(assets.count(), 12)
        for asset in assets:
            with self.subTest(asset=asset.asset_code):
                self.assertTrue(asset.summary)
                self.assertTrue(asset.network_notes)
                self.assertGreaterEqual(asset.latitude, -90)
                self.assertLessEqual(asset.latitude, 90)
                self.assertGreaterEqual(asset.longitude, -180)
                self.assertLessEqual(asset.longitude, 180)
                self.assertTrue(
                    asset.portrait.startswith(
                        "https://res.cloudinary.com/bobzlwnj/image/upload/"
                    )
                )
                self.assertEqual(asset.portrait_url, asset.portrait)

    def test_initial_network_includes_directives_and_archive_records(self):
        self.assertEqual(Directive.objects.filter(is_active=True).count(), 4)
        self.assertEqual(ArchiveDocument.objects.filter(is_visible=True).count(), 4)


class HamAccessTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="network-reader",
            password="correct-horse-battery-staple",
        )

    def test_ham_route_looks_missing_without_clearance(self):
        self.assertEqual(self.client.get(reverse("ham:dashboard")).status_code, 404)
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("ham:dashboard")).status_code, 404)

    def test_ham_navigation_is_hidden_without_clearance(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, reverse("ham:dashboard"))
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, reverse("ham:dashboard"))

    def test_enlightened_account_sees_navigation_and_network_records(self):
        HamClearance.objects.create(user=self.user, is_enlightened=True)
        self.client.force_login(self.user)

        header_response = self.client.get(reverse("home"))
        response = self.client.get(reverse("ham:dashboard"))

        self.assertContains(header_response, reverse("ham:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The network is awake")
        self.assertContains(response, '<body class="d-flex flex-column min-vh-100 ham-page">')
        self.assertContains(response, "HAM-ATH-042")
        self.assertContains(response, "The Spoon Protocol")
        self.assertContains(response, "maplibre-gl-leaflet")
        self.assertContains(response, "decentralized vampire network")
        self.assertContains(
            response,
            "Lena from HR says we should stop killing people cuz Legal is mad about it.",
        )
        self.assertContains(response, "One is cursed only in mono")
        self.assertContains(response, "Positions are approximate. Accuracy encourages paperwork.")
        self.assertNotContains(
            response,
            "Locations approximate // last reviewed after sundown",
        )
        self.assertContains(
            response,
            'id="asset-dossier" class="ham-dossier" aria-live="polite" tabindex="0"',
        )

        map_script = Path(finders.find("ham/js/ham.js")).read_text()
        self.assertIn("tiles.openfreemap.org/styles/dark", map_script)
        self.assertNotIn("tile.openstreetmap.org", map_script)
        self.assertIn("maxBoundsViscosity: 1", map_script)
        self.assertIn("inertia: false", map_script)
        self.assertNotIn("ham-spectacle-muted", map_script)

    def test_asset_query_selects_a_visible_dossier(self):
        HamClearance.objects.create(user=self.user, is_enlightened=True)
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("ham:dashboard"),
            {"asset": "HAM-VAN-001"},
        )

        self.assertEqual(response.context["selected_asset"].asset_code, "HAM-VAN-001")
        self.assertContains(response, "Edith Pike")
