"""Models for location-related workflows."""

from django.db import models
from django.contrib.auth.models import User

from apps.common.models import TimeStampedModel


class City(TimeStampedModel):
    """Geographic city for general city-level prayer timings."""
    class TimetablePolicy(models.TextChoices):
        ANNUAL_UPLOAD = "ANNUAL_UPLOAD", "Annual Upload Required"
        CONTINUE_PREVIOUS = "CONTINUE_PREVIOUS", "Continue Previous Timetable Until Replaced"
        ASTRONOMICAL = "ASTRONOMICAL", "Astronomical Calculation (Future)"
        AUTHORITY = "AUTHORITY", "Official Authority Source (Future)"

    name = models.CharField(max_length=100, unique=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")
    
    timetable_policy = models.CharField(
        max_length=30, 
        choices=TimetablePolicy.choices, 
        default=TimetablePolicy.ANNUAL_UPLOAD
    )
    acknowledged_timetable_year = models.IntegerField(null=True, blank=True)
    maghrib_congregation_offset = models.IntegerField(default=1)
    maghrib_auto_congregation_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Cities"

    def __str__(self) -> str:
        return self.name


class CityPrayerTiming(TimeStampedModel):
    """Citywide standard daily or calendar-specific prayer timings."""

    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="prayer_timings",
    )
    calendar_date = models.DateField(
        null=True,
        blank=True,
        help_text="Null for baseline daily timing defaults. Populated for specific calendar dates.",
    )
    fajr_time = models.TimeField()
    dhuhr_time = models.TimeField()
    asr_time = models.TimeField()
    maghrib_time = models.TimeField()
    isha_time = models.TimeField()

    class Meta:
        ordering = ["calendar_date", "city"]
        indexes = [
            models.Index(fields=["city", "calendar_date"]),
        ]

    def __str__(self) -> str:
        date_str = self.calendar_date.strftime("%Y-%m-%d") if self.calendar_date else "Default"
        return f"{self.city.name} timings ({date_str})"


class CityDailyPrayerTiming(TimeStampedModel):
    """Daily authoritative citywide prayer times imported from a CSV calendar."""

    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="daily_prayer_timings",
    )
    date = models.DateField(db_index=True)
    fajr_time = models.TimeField()
    sunrise_time = models.TimeField()
    dhuhr_time = models.TimeField()
    asr_time = models.TimeField()
    maghrib_time = models.TimeField()
    isha_time = models.TimeField()

    class Meta:
        ordering = ["date", "city"]
        unique_together = ("city", "date")
        indexes = [
            models.Index(fields=["city", "date"]),
        ]

    def __str__(self) -> str:
        return f"{self.city.name} timings ({self.date.strftime('%Y-%m-%d')})"


class CityCalendarImportLog(TimeStampedModel):
    """Audit log tracking daily prayer calendar imports by admins."""

    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="calendar_imports",
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="calendar_imports",
    )
    filename = models.CharField(max_length=255)
    rows_processed = models.IntegerField()
    rows_created = models.IntegerField()
    rows_updated = models.IntegerField()
    rows_skipped = models.IntegerField()  # Unchanged rows
    status = models.CharField(
        max_length=20,
        choices=[("success", "Success"), ("failed", "Failed")],
        default="success",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Import for {self.city.name} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
