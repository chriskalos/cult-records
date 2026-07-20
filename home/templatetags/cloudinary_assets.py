from django import template

from cultrecords.cloudinary_assets import cloudinary_image_url


register = template.Library()


@register.simple_tag
def cloudinary_image(public_id, width=None):
    return cloudinary_image_url(public_id, width=width)
