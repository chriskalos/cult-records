from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from home.models import Product

from .forms import ReviewForm
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
        self.assertEqual(review.status, Review.Status.PENDING)
        self.assertEqual(review.rejection_reason, "")
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

    def test_rejection_reason_is_cleared_for_non_rejected_reviews(self):
        review = Review.objects.create(
            product=self.product,
            author=self.user,
            rating=4,
            status=Review.Status.APPROVED,
            rejection_reason="This should not remain.",
        )

        self.assertEqual(review.rejection_reason, "")

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
        self.assertContains(response, 'data-product-format="CD"')
        self.assertContains(response, "product-media__cd-case")
        self.assertContains(response, "/static/home/js/product-media.js")

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

    def test_hidden_product_returns_not_found(self):
        self.product.is_visible = False
        self.product.save(update_fields=("is_visible",))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_catalogue_cards_link_to_product_detail_pages(self):
        response = self.client.get(reverse("home"))

        self.assertContains(
            response,
            reverse("product_page:detail", args=["MDEVCTRYLP"]),
        )


class ReviewFormTests(TestCase):
    def test_comment_is_optional_and_whitespace_becomes_empty(self):
        form = ReviewForm({"rating": "4", "comment": "   "})

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["comment"], "")

    def test_comment_rejects_more_than_2000_characters(self):
        form = ReviewForm({"rating": "4", "comment": "x" * 2001})

        self.assertFalse(form.is_valid())
        self.assertIn("2000 characters", form.errors["comment"][0])

    def test_rating_requires_a_whole_number_from_one_to_five(self):
        for rating in ("0", "3.5", "6"):
            with self.subTest(rating=rating):
                form = ReviewForm({"rating": rating, "comment": ""})
                self.assertFalse(form.is_valid())


class ReviewPageTests(TestCase):
    def setUp(self):
        self.product = Product.objects.get(product_id="MDEVCTRYLP")
        self.detail_url = reverse(
            "product_page:detail",
            args=[self.product.product_id],
        )
        self.create_url = reverse(
            "product_page:review_create",
            args=[self.product.product_id],
        )
        self.user = get_user_model().objects.create_user(
            username="current-user",
            password="test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )

    def test_anonymous_page_shows_empty_state_and_inactive_form(self):
        response = self.client.get(self.detail_url)

        self.assertContains(response, "No reviews yet.")
        self.assertContains(response, "Sign in to leave a review")
        self.assertContains(response, "<fieldset disabled>")
        self.assertContains(
            response,
            f'{reverse("accounts:login")}?next=/products/MDEVCTRYLP/%23your-review',
        )
        self.assertNotContains(response, self.create_url)

    def test_review_sign_in_returns_to_the_product(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "user1",
                "password": "user1",
                "next": f"{self.detail_url}#your-review",
            },
        )

        self.assertRedirects(
            response,
            f"{self.detail_url}#your-review",
            fetch_redirect_response=False,
        )

    def test_anonymous_user_cannot_submit_a_review(self):
        response = self.client.post(
            self.create_url,
            {"rating": "5", "comment": "Excellent."},
        )

        self.assertRedirects(
            response,
            f"/accounts/login/?next={self.create_url}",
            fetch_redirect_response=False,
        )
        self.assertFalse(Review.objects.exists())

    def test_authenticated_user_can_submit_a_review(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.create_url,
            {"rating": "5", "comment": "  Excellent.  "},
            follow=True,
        )

        review = Review.objects.get(product=self.product, author=self.user)
        self.assertRedirects(
            response,
            f"{self.detail_url}#your-review",
            fetch_redirect_response=False,
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Excellent.")
        self.assertEqual(review.status, Review.Status.PENDING)
        self.assertContains(
            response,
            "Your review was submitted and will go live once it is approved.",
        )
        self.assertContains(response, "Pending approval")

    def test_invalid_review_redisplays_the_bound_form(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.create_url,
            {"rating": "6", "comment": "Invalid rating."},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Select a valid choice")
        self.assertFalse(Review.objects.exists())

    def test_creation_endpoint_does_not_create_a_second_review(self):
        Review.objects.create(product=self.product, author=self.user, rating=3)
        self.client.force_login(self.user)

        response = self.client.post(
            self.create_url,
            {"rating": "5", "comment": "Replacement."},
        )

        self.assertRedirects(
            response,
            self.detail_url,
            fetch_redirect_response=False,
        )
        self.assertEqual(Review.objects.filter(author=self.user).count(), 1)
        self.assertEqual(Review.objects.get(author=self.user).rating, 3)

    def test_existing_review_becomes_your_review_section(self):
        review = Review.objects.create(
            product=self.product,
            author=self.user,
            rating=4,
            comment="My review.",
        )
        self.client.force_login(self.user)

        response = self.client.get(self.detail_url)

        self.assertContains(response, "Your Review")
        self.assertContains(response, "My review.")
        self.assertContains(response, "Edit")
        self.assertContains(response, f"?edit_review=1#your-review")
        self.assertNotContains(
            response,
            reverse(
                "product_page:review_delete",
                args=[self.product.product_id, review.pk],
            ),
        )

    def test_edit_button_replaces_review_with_editable_form(self):
        review = Review.objects.create(
            product=self.product,
            author=self.user,
            rating=4,
            comment="Original review.",
        )
        self.client.force_login(self.user)

        response = self.client.get(self.detail_url, {"edit_review": "1"})

        self.assertContains(response, "Original review.")
        self.assertContains(response, "Save changes")
        self.assertContains(response, "Cancel")
        self.assertContains(response, "Delete review")
        self.assertContains(
            response,
            reverse(
                "product_page:review_edit",
                args=[self.product.product_id, review.pk],
            ),
        )

    def test_user_can_edit_every_review_field(self):
        review = Review.objects.create(
            product=self.product,
            author=self.user,
            rating=2,
            comment="Original review.",
            status=Review.Status.REJECTED,
            rejection_reason="Add more context.",
        )
        self.client.force_login(self.user)
        edit_url = reverse(
            "product_page:review_edit",
            args=[self.product.product_id, review.pk],
        )

        response = self.client.post(
            edit_url,
            {"rating": "5", "comment": "Updated review."},
            follow=True,
        )

        review.refresh_from_db()
        self.assertRedirects(
            response,
            f"{self.detail_url}#your-review",
            fetch_redirect_response=False,
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, "Updated review.")
        self.assertEqual(review.status, Review.Status.PENDING)
        self.assertEqual(review.rejection_reason, "")
        self.assertContains(
            response,
            "Your review was updated and will go live again once it is approved.",
        )

    def test_rejected_review_reason_is_visible_only_in_the_owners_section(self):
        Review.objects.create(
            product=self.product,
            author=self.user,
            rating=2,
            comment="Not for the public list.",
            status=Review.Status.REJECTED,
            rejection_reason="Please keep the language constructive.",
        )
        self.client.force_login(self.user)

        response = self.client.get(self.detail_url)

        self.assertContains(response, "Rejected")
        self.assertContains(response, "Please keep the language constructive.")
        self.assertNotContains(response, "from 1 review")

    def test_user_cannot_edit_someone_elses_review(self):
        review = Review.objects.create(
            product=self.product,
            author=self.other_user,
            rating=4,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "product_page:review_edit",
                args=[self.product.product_id, review.pk],
            ),
            {"rating": "1", "comment": "Changed."},
        )

        self.assertEqual(response.status_code, 404)
        review.refresh_from_db()
        self.assertEqual(review.rating, 4)

    def test_user_can_delete_their_review_with_post(self):
        review = Review.objects.create(
            product=self.product,
            author=self.user,
            rating=4,
        )
        self.client.force_login(self.user)
        delete_url = reverse(
            "product_page:review_delete",
            args=[self.product.product_id, review.pk],
        )

        get_response = self.client.get(delete_url)
        post_response = self.client.post(delete_url)

        self.assertEqual(get_response.status_code, 405)
        self.assertRedirects(
            post_response,
            f"{self.detail_url}#reviews",
            fetch_redirect_response=False,
        )
        self.assertFalse(Review.objects.filter(pk=review.pk).exists())

    def test_user_cannot_delete_someone_elses_review(self):
        review = Review.objects.create(
            product=self.product,
            author=self.other_user,
            rating=4,
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse(
                "product_page:review_delete",
                args=[self.product.product_id, review.pk],
            )
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Review.objects.filter(pk=review.pk).exists())

    def test_average_count_and_list_use_approved_reviews(self):
        newest = Review.objects.create(
            product=self.product,
            author=self.other_user,
            rating=3,
            comment="Newest approved review.",
            status=Review.Status.APPROVED,
        )
        oldest_user = get_user_model().objects.create_user(username="oldest-user")
        oldest = Review.objects.create(
            product=self.product,
            author=oldest_user,
            rating=5,
            comment="Oldest approved review.",
            status=Review.Status.APPROVED,
        )
        hidden_user = get_user_model().objects.create_user(username="hidden-user")
        Review.objects.create(
            product=self.product,
            author=hidden_user,
            rating=1,
            comment="Unapproved review.",
            status=Review.Status.PENDING,
        )
        Review.objects.filter(pk=oldest.pk).update(created_at="2026-01-01T00:00:00Z")
        Review.objects.filter(pk=newest.pk).update(created_at="2026-02-01T00:00:00Z")

        response = self.client.get(self.detail_url)
        content = response.content.decode()

        self.assertContains(response, "4.0 / 5")
        self.assertContains(response, "from 2 reviews")
        self.assertNotContains(response, "Unapproved review.")
        self.assertLess(
            content.index("Newest approved review."),
            content.index("Oldest approved review."),
        )
