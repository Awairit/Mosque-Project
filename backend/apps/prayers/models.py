"""Models for prayer-related workflows."""

from django.contrib.auth.models import User
from django.db import models

from apps.common.models import TimeStampedModel
from apps.mosques.models import Mosque


class PrayerTiming(TimeStampedModel):
    """Congregation (jamaat) timings for an approved Mosque."""

    class CongregationMode(models.TextChoices):
        MANUAL = "manual", "Manual Input"
        CITY_OFFSET = "city_offset", "City Offset"

    mosque = models.OneToOneField(
        Mosque,
        on_delete=models.CASCADE,
        related_name="prayer_timing",
    )
    fajr_time = models.TimeField()
    dhuhr_time = models.TimeField()
    asr_time = models.TimeField()
    maghrib_time = models.TimeField()
    isha_time = models.TimeField()
    jumuah_time = models.TimeField()
    effective_from = models.DateField()
    maghrib_congregation_mode = models.CharField(
        max_length=20,
        choices=CongregationMode.choices,
        default=CongregationMode.MANUAL,
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_prayer_timings",
    )

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["effective_from"]),
        ]

    def __str__(self) -> str:
        return f"Timings for {self.mosque.mosque_name}"
