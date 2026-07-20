from urllib.parse import quote

from django.conf import settings


def cloudinary_image_url(public_id, *, width=None, image_format=None):
    """Build an optimized HTTPS delivery URL for a public Cloudinary image."""
    transformations = ["f_auto", "q_auto"]
    if width:
        transformations.extend(("c_scale", f"w_{int(width)}"))

    safe_public_id = quote(public_id.strip("/"), safe="/")
    suffix = f".{image_format.lstrip('.')}" if image_format else ""
    transformation = ",".join(transformations)
    return (
        f"https://res.cloudinary.com/{settings.CLOUDINARY_CLOUD_NAME}/"
        f"image/upload/{transformation}/{safe_public_id}{suffix}"
    )
