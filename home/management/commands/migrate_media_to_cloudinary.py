from pathlib import PurePosixPath
from urllib.parse import quote, urljoin, urlsplit

from cloudinary import api, uploader
from cloudinary.exceptions import NotFound
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ham.models import HumanAsset
from home.models import Product


class Command(BaseCommand):
    help = "Copy legacy Django media files from the live site into Cloudinary."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear-missing",
            action="store_true",
            help="Clear database references when a legacy file already returns 404.",
        )

    @staticmethod
    def _asset_parts(name):
        path = PurePosixPath(name)
        image_format = path.suffix.lstrip(".") or None
        public_id = str(path.with_suffix("")) if image_format else str(path)
        return public_id, image_format

    def _clear_reference(self, instance, field_name, current_name):
        type(instance).objects.filter(pk=instance.pk).update(**{field_name: ""})
        self.stderr.write(
            self.style.WARNING(
                f"Cleared missing legacy media reference {current_name}."
            )
        )
        return "cleared"

    def _migrate_field(self, instance, field_name, origin, clear_missing):
        field = getattr(instance, field_name)
        if not field:
            return False

        current_name = field.name
        public_id, current_format = self._asset_parts(current_name)
        try:
            result = api.resource(public_id, resource_type="image")
        except NotFound:
            if not origin:
                if clear_missing:
                    return self._clear_reference(
                        instance,
                        field_name,
                        current_name,
                    )
                raise CommandError(
                    f"CLOUDINARY_MEDIA_MIGRATION_ORIGIN is required to copy {current_name}."
                )
            source_url = urljoin(origin, quote(current_name, safe="/"))
            try:
                result = uploader.upload(
                    source_url,
                    public_id=public_id,
                    resource_type="image",
                    type="upload",
                    overwrite=False,
                    unique_filename=False,
                    tags=["cult-records", "legacy-media"],
                )
            except NotFound:
                if not clear_missing:
                    raise CommandError(
                        f"The legacy media file no longer exists at {source_url}."
                    )
                return self._clear_reference(instance, field_name, current_name)

        stored_format = result.get("format") or current_format
        stored_name = (
            f"{result['public_id']}.{stored_format}"
            if stored_format
            else result["public_id"]
        )
        if stored_name != current_name:
            type(instance).objects.filter(pk=instance.pk).update(
                **{field_name: stored_name}
            )
        self.stdout.write(f"Cloudinary has {stored_name}")
        return "verified"

    def handle(self, *args, **options):
        if not settings.CLOUDINARY_URL:
            raise CommandError("CLOUDINARY_URL is required to migrate media files.")

        origin = settings.CLOUDINARY_MEDIA_MIGRATION_ORIGIN
        if origin:
            origin = origin.rstrip("/") + "/"
        if origin and urlsplit(origin).scheme != "https":
            raise CommandError("CLOUDINARY_MEDIA_MIGRATION_ORIGIN must use HTTPS.")

        verified = 0
        cleared = 0
        for product in Product.objects.exclude(uploaded_image="").iterator():
            result = self._migrate_field(
                product,
                "uploaded_image",
                origin,
                options["clear_missing"],
            )
            verified += result == "verified"
            cleared += result == "cleared"
        for asset in HumanAsset.objects.exclude(uploaded_portrait="").iterator():
            result = self._migrate_field(
                asset,
                "uploaded_portrait",
                origin,
                options["clear_missing"],
            )
            verified += result == "verified"
            cleared += result == "cleared"

        self.stdout.write(
            self.style.SUCCESS(
                f"Verified {verified} uploaded media files in Cloudinary; "
                f"cleared {cleared} missing legacy references."
            )
        )
