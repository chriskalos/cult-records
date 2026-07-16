from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from home.models import Product


class ComponentGalleryTests(TestCase):
    def test_gallery_uses_shared_layout_and_components(self):
        Product.objects.create(
            product_id="VISUALCD",
            artist="A Cult Records",
            title="Visual Test Record",
            description="A catalogue card shown in the component gallery.",
            genre="Electronic",
            product_type=Product.ProductType.CD,
            price=Decimal("6.99"),
        )

        response = self.client.get(reverse("visuals:component_gallery"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "visuals/component_gallery.html")
        self.assertTemplateUsed(response, "home/base.html")
        self.assertTemplateUsed(response, "home/includes/header.html")
        self.assertTemplateUsed(response, "home/includes/footer.html")
        self.assertTemplateUsed(response, "home/includes/product_card.html")
        self.assertContains(response, "Visual Test Record")
        self.assertContains(response, 'data-product-format="LP"')
        self.assertContains(response, 'data-product-format="CD"')
        self.assertContains(response, "css/style.css")
        self.assertContains(response, "Account")
        self.assertContains(response, 'data-bs-toggle="dropdown"')
        self.assertContains(response, "#780D19")
        self.assertContains(
            response,
            "Bringing you the best of music at the best price... If you're willing to pay it.",
        )

    def test_gallery_works_without_catalogue_products(self):
        Product.objects.all().delete()

        response = self.client.get(reverse("visuals:component_gallery"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Add an LP product to preview its shared product card.")
        self.assertContains(response, "Add a CD product to preview its shared product card.")
