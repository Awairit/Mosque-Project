import logging
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from cloudinary_storage.storage import MediaCloudinaryStorage
from cloudinary.exceptions import Error as CloudinaryError

logger = logging.getLogger(__name__)


class SafeCloudinaryStorage(MediaCloudinaryStorage):
    """Custom Cloudinary storage that verifies settings and handles upload failures gracefully."""

    def __init__(self, *args, **kwargs):
        config = getattr(settings, "CLOUDINARY_STORAGE", {})
        cloud_name = config.get("CLOUD_NAME")
        api_key = config.get("API_KEY")
        api_secret = config.get("API_SECRET")

        if not cloud_name or not api_key or not api_secret:
            raise ImproperlyConfigured(
                "Cloudinary credentials are not properly configured. "
                "Ensure CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, and "
                "CLOUDINARY_API_SECRET are set."
            )

        if "invalid" in str(cloud_name).lower() or "invalid" in str(api_key).lower():
            raise ImproperlyConfigured("Cloudinary configuration contains invalid credentials.")

        super().__init__(*args, **kwargs)

    def _save(self, name, content):
        try:
            return super()._save(name, content)
        except Exception as exc:
            logger.error(f"Cloudinary upload failed for {name}: {str(exc)}")
            # Handle upload failure gracefully (e.g. raise a cleaner exception or bubble up)
            raise IOError(f"Failed to upload file to Cloudinary: {str(exc)}") from exc
