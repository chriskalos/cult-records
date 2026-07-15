from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from home.models import Product

from .models import ProductPage, Review


class ProductPageModelTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            product_id="DETAILLP",
            artist="Test Artist",
            title="Detailed Album",
            description="Short description.",
            genre="Electronic",
            product_type=Product.ProductType.LP,
            price=Decimal("19.99"),
        )

    def test_product_page_uses_product_as_its_primary_key(self):
        page = ProductPage.objects.create(
            product=self.product,
            long_description="First paragraph.\n\nSecond paragraph.",
            release_date=date(2026, 7, 15),
            tracks=["Opening Track", "Closing Track"],
        )

        page.full_clean()
        self.assertEqual(page.pk, self.product.pk)
        self.assertEqual(page.product, self.product)
        self.assertEqual(page.release_date, date(2026, 7, 15))
        self.assertEqual(page.tracks, ["Opening Track", "Closing Track"])

    def test_supplementary_fields_are_optional(self):
        page = ProductPage(product=self.product)

        page.full_clean()
        page.save()

        self.assertEqual(page.long_description, "")
        self.assertIsNone(page.release_date)
        self.assertEqual(page.tracks, [])

    def test_tracks_must_be_a_list_of_non_empty_names(self):
        invalid_values = ["Opening Track", ["Opening Track", "   "]]

        for value in invalid_values:
            with self.subTest(value=value):
                page = ProductPage(product=self.product, tracks=value)
                with self.assertRaises(ValidationError):
                    page.full_clean()

    def test_existing_catalogue_pages_copy_the_short_description(self):
        product = Product.objects.get(product_id="MDEVCTRYLP")

        self.assertEqual(product.page.long_description, product.description)

    def test_deleting_product_deletes_its_page(self):
        ProductPage.objects.create(product=self.product)

        self.product.delete()

        self.assertFalse(ProductPage.objects.filter(pk="DETAILLP").exists())


class ReviewModelTests(TestCase):
    def setUp(self):
        self.product = Product.objects.get(product_id="MDEVCTRYLP")
        self.user = get_user_model().objects.create_user(
            username="reviewer",
            password="test-password",
        )

    def test_review_stores_rating_comment_and_moderation_data(self):
        review = Review.objects.create(
            product=self.product,
            author=self.user,
            rating=5,
            comment="  Excellent album.  ",
        )

        self.assertEqual(review.comment, "Excellent album.")
        self.assertTrue(review.is_approved)
        self.assertIsNotNone(review.created_at)
        self.assertIsNotNone(review.updated_at)

    def test_comment_may_be_empty_and_has_a_2000_character_limit(self):
        empty_review = Review(
            product=self.product,
            author=self.user,
            rating=4,
            comment="   ",
        )
        empty_review.full_clean()
        self.assertEqual(empty_review.comment, "")

        empty_review.comment = "x" * 2001
        with self.assertRaises(ValidationError):
            empty_review.full_clean()

    def test_rating_must_be_between_one_and_five(self):
        for rating in (0, 6):
            with self.subTest(rating=rating):
                review = Review(
                    product=self.product,
                    author=self.user,
                    rating=rating,
                )
                with self.assertRaises(ValidationError):
                    review.full_clean()

    def test_user_can_only_review_a_product_once(self):
        Review.objects.create(product=self.product, author=self.user, rating=4)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Review.objects.create(product=self.product, author=self.user, rating=5)

    def test_deleting_user_deletes_their_reviews(self):
        review = Review.objects.create(
            product=self.product,
            author=self.user,
            rating=4,
        )

        self.user.delete()

        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

    def test_deleting_product_deletes_its_reviews(self):
        review = Review.objects.create(
            product=self.product,
            author=self.user,
            rating=4,
        )

        self.product.delete()

        self.assertFalse(Review.objects.filter(pk=review.pk).exists())


class ProductDetailPageTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            product_id="PAGECD",
            image="home/images/products/madeon-victory.jpg",
            artist="Test Artist",
            title="Page Album",
            description="Short catalogue description.",
            genre="Electronic",
            product_type=Product.ProductType.CD,
            price=Decimal("6.99"),
        )
        self.url = reverse("product_page:detail", args=[self.product.product_id])

    def test_detail_page_displays_product_and_supplementary_data(self):
        ProductPage.objects.create(
            product=self.product,
            long_description="First paragraph.\n\nSecond paragraph.",
            release_date=date(2026, 7, 15),
            tracks=["Opening Track", "Closing Track"],
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "product_page/detail.html")
        self.assertContains(response, "Page Album")
        self.assertContains(response, "Test Artist")
        self.assertContains(response, "Electronic")
        self.assertContains(response, "15 July 2026")
        self.assertContains(response, "First paragraph.")
        self.assertContains(response, "Second paragraph.")
        self.assertContains(response, "Opening Track")
        self.assertContains(response, "6.99€")
        self.assertContains(response, "Add to cart")

    def test_detail_page_falls_back_when_supplementary_data_is_missing(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Short catalogue description.", count=2)
        self.assertNotContains(response, "Track listing")
        self.assertNotContains(response, "Release date:")

    def test_artist_breadcrumb_links_to_filtered_catalogue(self):
        response = self.client.get(self.url)

        self.assertContains(response, "/search/?artist=Test%20Artist")

    def test_unknown_product_returns_not_found(self):
        response = self.client.get(
            reverse("product_page:detail", args=["UNKNOWNPRODUCT"])
        )

        self.assertEqual(response.status_code, 404)

    def test_catalogue_cards_link_to_product_detail_pages(self):
        response = self.client.get(reverse("home"))

        self.assertContains(
            response,
            reverse("product_page:detail", args=["MDEVCTRYLP"]),
        )
