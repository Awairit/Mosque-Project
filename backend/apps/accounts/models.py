"""Models for account-related workflows."""

from django.contrib.auth.models import User
from django.db import models

from apps.common.models import TimeStampedModel
from apps.mosques.models import Mosque


class MosqueAdmin(TimeStampedModel):
    """Admin profile for a verified Mosque, linked to a Django User."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="mosque_admin",
    )
    mosque = models.ForeignKey(
        Mosque,
        on_delete=models.CASCADE,
        related_name="admins",
    )
    mobile_number = models.CharField(max_length=32, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mobile_number", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.mosque.mosque_name}"
