from pathlib import Path

from cloudinary import uploader
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


class Command(BaseCommand):
    help = "Upload the project's version-controlled image assets to Cloudinary."

    def handle(self, *args, **options):
        if not settings.CLOUDINARY_URL:
            raise CommandError("CLOUDINARY_URL is required to upload project images.")

        assets = [
            (
                settings.BASE_DIR
                / "home/static/home/images/brand/cult-records-logo-512.png",
                "cult-records/brand/cult-records-logo",
            ),
        ]
        assets.extend(
            (path, f"cult-records/products/{path.stem}")
            for path in sorted(
                (settings.BASE_DIR / "home/static/home/images/products").glob("*")
            )
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        assets.extend(
            (path, f"cult-records/ham/{path.stem}")
            for path in sorted(
                (settings.BASE_DIR / "ham/static/ham/images/assets").glob("*")
            )
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )

        missing = [
            str(path.relative_to(settings.BASE_DIR))
            for path, _ in assets
            if not path.exists()
        ]
        if missing:
            raise CommandError(f"Missing source images: {', '.join(missing)}")

        for path, public_id in assets:
            uploader.upload(
                str(Path(path)),
                public_id=public_id,
                resource_type="image",
                type="upload",
                overwrite=True,
                invalidate=True,
                unique_filename=False,
                tags=["cult-records", "project-source"],
            )
            self.stdout.write(f"Uploaded {public_id}")

        self.stdout.write(self.style.SUCCESS(f"Uploaded {len(assets)} project images."))
