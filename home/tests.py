from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.urls import reverse

from .models import BundleItem, Product


class ProductModelTests(TestCase):
    def test_product_stores_catalogue_data(self):
        product = Product.objects.create(
            product_id="TESTCATLP",
            image="home/images/products/madeon-victory.jpg",
            artist="Madeon",
            title="Victory",
            description="Madeon's 2026 album Victory on vinyl LP.",
            genre="Electronic",
            product_type=Product.ProductType.LP,
            price=Decimal("14.99"),
        )

        product.full_clean()
        self.assertEqual(product.pk, "TESTCATLP")
        self.assertEqual(product.image, "home/images/products/madeon-victory.jpg")
        self.assertEqual(product.artist, "Madeon")
        self.assertEqual(product.genre, "Electronic")
        self.assertEqual(product.product_type, "LP")
        self.assertEqual(product.price, Decimal("14.99"))
        self.assertTrue(product.is_visible)
        self.assertFalse(product.uploaded_image)
        self.assertEqual(str(product), "Madeon - Victory")

    def test_product_id_rejects_invalid_characters(self):
        product = Product(
            product_id="invalid-id",
            artist="Placeholder Artist",
            title="Placeholder Title",
            description="Placeholder Description",
            product_type=Product.ProductType.CD,
            price=Decimal("29.99"),
        )

        with self.assertRaises(ValidationError):
            product.full_clean()

    def test_product_type_choices_are_fixed(self):
        self.assertEqual(
            Product.ProductType.values,
            ["LP", "CD", "BUNDLE", "MERCH"],
        )

    def test_bundle_items_require_non_bundle_components(self):
        bundle = Product.objects.create(
            product_id="BUNDLEONE",
            artist="Cult Records",
            title="First bundle",
            description="A bundle.",
            product_type=Product.ProductType.BUNDLE,
            price=Decimal("20.00"),
        )
        nested_bundle = Product.objects.create(
            product_id="BUNDLETWO",
            artist="Cult Records",
            title="Second bundle",
            description="Another bundle.",
            product_type=Product.ProductType.BUNDLE,
            price=Decimal("30.00"),
        )

        with self.assertRaises(ValidationError):
            BundleItem.objects.create(
                bundle=bundle,
                component=nested_bundle,
                quantity=1,
                position=1,
            )

    def test_component_deletion_is_protected_while_used_by_a_bundle(self):
        component = Product.objects.create(
            product_id="COMPONENTLP",
            artist="Test Artist",
            title="Component",
            description="A component.",
            product_type=Product.ProductType.LP,
            price=Decimal("10.00"),
        )
        bundle = Product.objects.create(
            product_id="PROTECTEDBUNDLE",
            artist="Cult Records",
            title="Protected bundle",
            description="A bundle.",
            product_type=Product.ProductType.BUNDLE,
            price=Decimal("15.00"),
        )
        BundleItem.objects.create(bundle=bundle, component=component)

        with self.assertRaises(ProtectedError):
            component.delete()

    def test_public_catalogue_excludes_hidden_products_and_incomplete_bundles(self):
        hidden_component = Product.objects.create(
            product_id="HIDDENCOMP",
            artist="Test Artist",
            title="Hidden component",
            description="Hidden.",
            product_type=Product.ProductType.CD,
            price=Decimal("8.00"),
            is_visible=False,
        )
        bundle = Product.objects.create(
            product_id="HIDDENBUNDLE",
            artist="Cult Records",
            title="Hidden component bundle",
            description="Bundle.",
            product_type=Product.ProductType.BUNDLE,
            price=Decimal("10.00"),
        )
        BundleItem.objects.create(bundle=bundle, component=hidden_component)

        public_products = Product.objects.public()

        self.assertNotIn(hidden_component, public_products)
        self.assertNotIn(bundle, public_products)


class HomePageTests(TestCase):
    def test_home_page_uses_reusable_layout(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home/index.html")
        self.assertTemplateUsed(response, "home/base.html")
        self.assertTemplateUsed(response, "home/includes/header.html")
        self.assertTemplateUsed(response, "home/includes/footer.html")
        self.assertTemplateUsed(response, "home/includes/product_card.html")

    def test_home_page_displays_products(self):
        response = self.client.get(reverse("home"))

        products = response.context["products"]
        self.assertEqual(products.count(), 29)
        self.assertContains(response, "Balu Brigada")
        self.assertContains(response, "chriskalos dot xyz")
        self.assertContains(response, "2026 album Victory on CD.")
        self.assertContains(response, "14.99€")
        self.assertContains(response, "6.99€")
        self.assertNotContains(response, "Placeholder Artist")
        self.assertContains(
            response,
            "/static/home/images/products/madeon-victory.jpg",
            count=2,
        )
        self.assertContains(
            response,
            "/static/home/images/products/cursed-locale-dance-w-me.jpg",
        )
        self.assertContains(response, "WOR$T GIRL IN AMERICA")
        self.assertContains(
            response,
            "/static/home/images/products/callinsick-doubling-down.jpg",
            count=2,
        )
        self.assertContains(response, 'data-product-format="LP"', count=13)
        self.assertContains(response, 'data-product-format="CD"', count=16)
        self.assertContains(response, 'class="product-media__cd-tab ', count=64)
        self.assertContains(
            response,
            "data-product-media data-product-format",
            count=29,
        )

    def test_header_contains_catalogue_search(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, f'action="{reverse("search:results")}"')
        self.assertContains(response, 'name="query"')

    def test_hidden_products_do_not_appear_on_the_home_page(self):
        product = Product.objects.get(product_id="MDEVCTRYLP")
        product.is_visible = False
        product.save(update_fields=("is_visible",))

        response = self.client.get(reverse("home"))

        self.assertNotContains(response, product.get_absolute_url())

    def test_shared_layout_applies_confirmed_identity(self):
        response = self.client.get(reverse("home"))

        self.assertContains(response, "/static/css/style.css")
        self.assertContains(response, "/static/home/js/product-media.js")
        self.assertContains(
            response,
            "/static/home/images/brand/cult-records-logo-64.png",
        )
        self.assertContains(response, "<span>Cult Records</span>", html=True)
        self.assertContains(response, "Account")
        self.assertContains(response, 'data-bs-toggle="dropdown"')
        self.assertContains(response, "Sign in")
        self.assertContains(response, "Register")
        self.assertContains(
            response,
            "Bringing you the best of music at the best price... If you're willing to pay it.",
        )
