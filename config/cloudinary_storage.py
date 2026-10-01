"""
A minimal Cloudinary media storage built directly on the ``cloudinary`` SDK.

Why not django-cloudinary-storage? Its releases do not clearly support the
``STORAGES`` setting that Django 4.2 introduced and Django 5.x requires, so
(as allowed by the project brief) this tiny backend talks to the ``cloudinary``
package directly. It gives the Honor Board exactly what it needs:

* upload the photo on save (``_save``) under a unique public id, so two uploads
  that happen to share a filename can never overwrite each other
* serve it from the Cloudinary CDN (``url``)
* avoid overwriting existing files (``exists``)
* remove it when the record is deleted (``delete``)

Configuration is automatic: the ``cloudinary`` SDK reads the CLOUDINARY_URL
environment variable (cloudinary://api_key:api_secret@cloud_name) the moment
it is imported, and settings.py only selects this backend when that variable
is set. The stored "name" is the public id *with* its extension, e.g.
``students/photo_a1b2c3.jpg``, which lets ``url()`` rebuild the delivery URL
without any extra API calls.
"""

import os
import uuid

import cloudinary
import cloudinary.api
import cloudinary.uploader
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import Storage

# f_auto/q_auto lets Cloudinary deliver an optimized format (WebP/AVIF) and
# quality to every browser. Available on the free plan.
DELIVERY_TRANSFORMS = "f_auto,q_auto"


class CloudinaryMediaStorage(Storage):
    """Stores images in Cloudinary and serves them from its CDN."""

    def __init__(self, folder="honor_board"):
        self.folder = folder.strip("/")
        if not os.environ.get("CLOUDINARY_URL"):
            # Defensive: settings only selects this backend when CLOUDINARY_URL
            # is set, so this should never trigger in practice.
            raise ImproperlyConfigured(
                "CloudinaryMediaStorage requires the CLOUDINARY_URL environment "
                "variable (cloudinary://api_key:api_secret@cloud_name)."
            )
        if not cloudinary.config().cloud_name:
            raise ImproperlyConfigured(
                "Cloudinary is not configured: could not read a cloud name from "
                "the CLOUDINARY_URL environment variable."
            )

    # -- helpers ------------------------------------------------------------
    def _split(self, name):
        """'students/photo.jpg' -> ('honor_board/students/photo', 'jpg')."""
        name = name.lstrip("/")
        if "." in name.rsplit("/", 1)[-1]:
            public_id, _, ext = name.rpartition(".")
        else:
            public_id, ext = name, ""
        if self.folder:
            public_id = f"{self.folder}/{public_id}"
        return public_id, ext.lower()

    # -- Django Storage API -------------------------------------------------
    def _open(self, name, mode="rb"):
        raise NotImplementedError(
            "CloudinaryMediaStorage does not support opening files directly; "
            "use url(name) to link to the CDN copy."
        )

    def _save(self, name, content):
        public_id, ext = self._split(name)
        # A random suffix makes every upload unique, so uploading two files that
        # share a filename (photo.jpg twice) never overwrites the first one.
        unique_suffix = uuid.uuid4().hex[:8]
        public_id = f"{public_id}_{unique_suffix}"
        if hasattr(content, "open"):
            content.open("rb")
        result = cloudinary.uploader.upload(
            content,
            public_id=public_id,
            resource_type="image",
            overwrite=False,
        )
        # Keep the stored name in sync with the format Cloudinary actually
        # saved (e.g. an uploaded HEIC stays .heic) and carry the unique suffix
        # over, so url() and delete() address the asset that was really
        # uploaded and stay truthful.
        stored_format = (result.get("format") or ext or "jpg").lower()
        base = name.rstrip("/")
        if ext:
            base = base.rsplit(".", 1)[0]
        return f"{base}_{unique_suffix}.{stored_format}"

    def exists(self, name):
        if not name:
            return False
        public_id, _ = self._split(name)
        try:
            cloudinary.api.resource(public_id, resource_type="image")
        except cloudinary.api.NotFound:
            return False
        return True

    def delete(self, name):
        if not name:
            return
        public_id, _ = self._split(name)
        try:
            cloudinary.uploader.destroy(public_id, resource_type="image")
        except Exception:  # noqa: BLE001 - never let a CDN hiccup break the admin
            pass

    def url(self, name):
        public_id, ext = self._split(name)
        ext = ext or "jpg"
        cloud_name = cloudinary.config().cloud_name
        if not cloud_name:
            raise ImproperlyConfigured("Cloudinary is not configured (missing cloud name).")
        return (
            f"https://res.cloudinary.com/{cloud_name}/image/upload/"
            f"{DELIVERY_TRANSFORMS}/{public_id}.{ext}"
        )
