from pathlib import PurePosixPath

import requests
from cloudinary import api, uploader
from cloudinary.exceptions import NotFound
from django.core.files.base import ContentFile
from django.core.files.storage import Storage

from .cloudinary_assets import cloudinary_image_url


class CloudinaryImageStorage(Storage):
    """Store Django ImageField files as Cloudinary image assets."""

    @staticmethod
    def _asset_parts(name):
        path = PurePosixPath(name)
        image_format = path.suffix.lstrip(".") or None
        public_id = str(path.with_suffix("")) if image_format else str(path)
        return public_id, image_format

    def _open(self, name, mode="rb"):
        if mode not in {"r", "rb"}:
            raise ValueError("Cloudinary images can only be opened for reading.")
        response = requests.get(self.url(name), timeout=30)
        response.raise_for_status()
        return ContentFile(response.content, name=name)

    def _save(self, name, content):
        public_id, _ = self._asset_parts(name)
        content.open()
        result = uploader.upload(
            content,
            public_id=public_id,
            resource_type="image",
            type="upload",
            overwrite=False,
            unique_filename=False,
        )
        return f"{result['public_id']}.{result['format']}"

    def delete(self, name):
        if not name:
            return
        public_id, _ = self._asset_parts(name)
        uploader.destroy(public_id, resource_type="image", invalidate=True)

    def exists(self, name):
        public_id, _ = self._asset_parts(name)
        try:
            api.resource(public_id, resource_type="image")
        except NotFound:
            return False
        return True

    def get_available_name(self, name, max_length=None):
        if max_length and len(name) > max_length:
            raise ValueError("The generated Cloudinary image name is too long.")
        return name

    def size(self, name):
        public_id, _ = self._asset_parts(name)
        return api.resource(public_id, resource_type="image")["bytes"]

    def url(self, name):
        public_id, image_format = self._asset_parts(name)
        return cloudinary_image_url(public_id, image_format=image_format)
