from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from zoneinfo import ZoneInfo
import datetime

from apps.mosques.models import Mosque


class JanazahNotice(models.Model):
    class GenderChoices(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"

    class StatusChoices(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        ARCHIVED = "archived", "Archived"

    # Core Relations
    mosque = models.ForeignKey(
        Mosque,
        on_delete=models.CASCADE,
        related_name="janazah_notices"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_janazahs"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_janazahs"
    )

    # Deceased Information
    deceased_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=GenderChoices.choices)
    age = models.IntegerField(null=True, blank=True)
    date_of_death = models.DateField()

    # Salah (Funeral Prayer) Details
    salah_date = models.DateField()
    salah_time = models.TimeField()
    salah_details = models.TextField(blank=True)

    # Burial Details
    burial_date = models.DateField(null=True, blank=True)
    burial_time = models.TimeField(null=True, blank=True)
    cemetery_name = models.CharField(max_length=255, blank=True)
    cemetery_address = models.TextField(blank=True)
    cemetery_gps_url = models.URLField(max_length=500, blank=True, null=True)

    # Family & Contact (With Privacy Controls)
    family_contact_name = models.CharField(max_length=255, blank=True)
    family_contact_phone = models.CharField(max_length=32, blank=True)
    publish_contact_info = models.BooleanField(default=False)

    # Status & Metadata
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT
    )
    version = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-salah_date", "-salah_time"]
        indexes = [
            models.Index(fields=["status", "salah_date"]),
            models.Index(fields=["mosque", "status"]),
        ]

    def __str__(self) -> str:
        return f"Janazah of {self.deceased_name} ({self.status})"

    def clean(self):
        super().clean()

        # Enforce date validations
        # Get localized date today
        if self.mosque and self.mosque.city_relation and self.mosque.city_relation.timezone:
            tz = ZoneInfo(self.mosque.city_relation.timezone)
            today = timezone.localtime(timezone.now()).astimezone(tz).date()
        else:
            today = timezone.localdate()

        # 1. Death date cannot be in the future
        if self.date_of_death and self.date_of_death > today:
            raise ValidationError({"date_of_death": "Date of death cannot be in the future."})

        # 2. Salah date must be on or after date of death
        if self.salah_date and self.date_of_death and self.salah_date < self.date_of_death:
            raise ValidationError({"salah_date": "Salah date cannot be before the date of death."})

        # 3. Burial date must be on or after salah date
        if self.burial_date and self.salah_date and self.burial_date < self.salah_date:
            raise ValidationError({"burial_date": "Burial date cannot be before the Salah date."})

    def save(self, *args, **kwargs):
        # Auto-update status times on state change
        if self.pk:
            orig = JanazahNotice.objects.get(pk=self.pk)
            if orig.status != self.status:
                if self.status == self.StatusChoices.PUBLISHED:
                    self.published_at = timezone.now()
                elif self.status == self.StatusChoices.CANCELLED:
                    self.cancelled_at = timezone.now()
                elif self.status == self.StatusChoices.ARCHIVED:
                    self.archived_at = timezone.now()
        else:
            if self.status == self.StatusChoices.PUBLISHED:
                self.published_at = timezone.now()

        # Perform validations before saving
        self.full_clean()
        super().save(*args, **kwargs)
