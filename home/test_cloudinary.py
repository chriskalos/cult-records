from io import StringIO
from unittest.mock import patch

from cloudinary.exceptions import NotFound
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from cultrecords.storage import CloudinaryImageStorage

from .models import Product


class CloudinaryImageStorageTests(SimpleTestCase):
    def setUp(self):
        self.storage = CloudinaryImageStorage()

    @patch("cultrecords.storage.uploader.upload")
    def test_save_uploads_an_image_under_its_generated_public_id(self, upload):
        upload.return_value = {
            "public_id": "products/TESTCD/random-id",
            "format": "webp",
        }

        name = self.storage.save(
            "products/TESTCD/random-id.png",
            ContentFile(b"image data", name="cover.png"),
        )

        self.assertEqual(name, "products/TESTCD/random-id.webp")
        self.assertEqual(upload.call_args.kwargs["public_id"], "products/TESTCD/random-id")
        self.assertFalse(upload.call_args.kwargs["overwrite"])

    def test_url_uses_optimized_secure_cloudinary_delivery(self):
        self.assertEqual(
            self.storage.url("products/TESTCD/random-id.png"),
            "https://res.cloudinary.com/bobzlwnj/image/upload/"
            "f_auto,q_auto/products/TESTCD/random-id.png",
        )

    @patch("cultrecords.storage.uploader.destroy")
    def test_delete_invalidates_the_cloudinary_asset(self, destroy):
        self.storage.delete("products/TESTCD/random-id.png")

        destroy.assert_called_once_with(
            "products/TESTCD/random-id",
            resource_type="image",
            invalidate=True,
        )

    @patch("cultrecords.storage.api.resource", side_effect=NotFound)
    def test_missing_cloudinary_asset_does_not_exist(self, resource):
        self.assertFalse(self.storage.exists("products/TESTCD/missing.png"))


@override_settings(
    CLOUDINARY_URL="cloudinary://example:example@example",
    CLOUDINARY_MEDIA_MIGRATION_ORIGIN="https://cult.example/media/",
)
class CloudinaryMigrationCommandTests(TestCase):
    @patch("home.management.commands.migrate_media_to_cloudinary.uploader.upload")
    @patch(
        "home.management.commands.migrate_media_to_cloudinary.api.resource",
        side_effect=NotFound,
    )
    def test_legacy_product_media_is_copied_from_the_live_site(
        self,
        resource,
        upload,
    ):
        product = Product.objects.get(product_id="MDEVCTRYCD")
        product.uploaded_image = "products/MDEVCTRYCD/legacy cover.png"
        product.save(update_fields=("uploaded_image",))
        upload.return_value = {
            "public_id": "products/MDEVCTRYCD/legacy cover",
            "format": "png",
        }

        call_command("migrate_media_to_cloudinary", stdout=StringIO())

        upload.assert_called_once()
        self.assertEqual(
            upload.call_args.args[0],
            "https://cult.example/media/products/MDEVCTRYCD/legacy%20cover.png",
        )
        self.assertEqual(
            upload.call_args.kwargs["public_id"],
            "products/MDEVCTRYCD/legacy cover",
        )

    @patch("home.management.commands.upload_project_images.uploader.upload")
    def test_project_source_images_are_uploaded_to_named_cloudinary_assets(self, upload):
        call_command("upload_project_images", stdout=StringIO())

        self.assertEqual(upload.call_count, 29)
        public_ids = {call.kwargs["public_id"] for call in upload.call_args_list}
        self.assertIn("cult-records/brand/cult-records-logo", public_ids)
        self.assertIn("cult-records/products/madeon-victory", public_ids)
        self.assertIn("cult-records/ham/adrian-voss", public_ids)

    @patch(
        "home.management.commands.migrate_media_to_cloudinary.uploader.upload",
        side_effect=NotFound,
    )
    @patch(
        "home.management.commands.migrate_media_to_cloudinary.api.resource",
        side_effect=NotFound,
    )
    def test_missing_legacy_media_reference_can_be_cleared(self, resource, upload):
        product = Product.objects.get(product_id="MDEVCTRYCD")
        product.uploaded_image = "products/MDEVCTRYCD/missing.png"
        product.save(update_fields=("uploaded_image",))

        call_command(
            "migrate_media_to_cloudinary",
            clear_missing=True,
            stdout=StringIO(),
            stderr=StringIO(),
        )

        product.refresh_from_db()
        self.assertFalse(product.uploaded_image)
