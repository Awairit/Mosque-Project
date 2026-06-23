"""Models for mosque-related workflows."""

from django.contrib.auth.models import User
from django.db import models
from django.core.files.storage import default_storage

from apps.common.models import TimeStampedModel


class Mosque(TimeStampedModel):
    """Approved mosque that is safe to expose through public APIs."""

    class MosqueStatus(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    class MosqueType(models.TextChoices):
        JAMA_MASJID = "jama_masjid", "Jama Masjid (Juma Mosque)"
        DAILY_PRAYER = "daily_prayer", "Daily Prayer Hall"
        MUSALLAH = "musallah", "Musallah (Prayer Room)"

    mosque_name = models.CharField(max_length=255)
    city = models.CharField(max_length=120, blank=True)
    city_relation = models.ForeignKey(
        "locations.City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mosques",
    )
    address = models.TextField(blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True
    )
    women_prayer_available = models.BooleanField(default=False)
    mosque_status = models.CharField(
        max_length=20,
        choices=MosqueStatus.choices,
        default=MosqueStatus.ACTIVE,
        db_index=True,
    )

    # Extended Profile Fields
    description = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=32, blank=True)
    website = models.URLField(max_length=255, blank=True)

    # Extended Facilities Fields
    parking_available = models.BooleanField(default=False)
    wudu_facility_available = models.BooleanField(default=False)
    wheelchair_accessible = models.BooleanField(default=False)
    profile_image = models.ImageField(
        upload_to="mosque_profiles/", null=True, blank=True
    )

    # Future Compatibility & Extra Features
    mosque_type = models.CharField(
        max_length=50,
        choices=MosqueType.choices,
        default=MosqueType.JAMA_MASJID,
    )
    separate_women_entrance = models.BooleanField(default=False)
    google_maps_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        ordering = ["mosque_name"]
        indexes = [
            models.Index(fields=["mosque_status", "city"]),
            models.Index(fields=["mosque_name", "city"]),
            models.Index(fields=["mosque_status", "city_relation"]),
            models.Index(fields=["mosque_name", "city_relation"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self) -> str:
        return self.mosque_name

    def save(self, *args, **kwargs):
        if (self.latitude is None or self.longitude is None) and self.google_maps_url:
            from apps.mosques.services import extract_coordinates_from_url
            lat, lon = extract_coordinates_from_url(self.google_maps_url)
            if lat is not None and lon is not None:
                self.latitude = lat
                self.longitude = lon
                
        # Dual-write synchronization
        if self.city_relation_id:
            from apps.locations.models import City
            city_obj = City.objects.filter(id=self.city_relation_id).first()
            if city_obj:
                self.city = city_obj.name
        elif self.city:
            from apps.locations.models import City
            import string
            normalized = " ".join(self.city.split()).strip(string.punctuation).lower()
            city_obj = City.objects.filter(name__iexact=normalized).first()
            if not city_obj:
                city_obj = City.objects.filter(name__icontains=normalized).first()
            if city_obj:
                self.city_relation = city_obj
                self.city = city_obj.name
                
        super().save(*args, **kwargs)


class MosqueRegistrationRequest(TimeStampedModel):
    """Public request submitted by someone who wants to register a mosque."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    mosque_name = models.CharField(max_length=255)
    admin_name = models.CharField(max_length=255, blank=True)
    mobile_number = models.CharField(max_length=32)
    city = models.CharField(max_length=120, blank=True)
    city_raw = models.CharField(max_length=120, blank=True)
    city_relation = models.ForeignKey(
        "locations.City",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registration_requests",
    )
    address = models.TextField(blank=True)
    google_maps_link = models.URLField(max_length=500, blank=True)
    google_maps_url = models.URLField(max_length=500, blank=True, null=True)
    women_prayer_available = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "city"]),
            models.Index(fields=["status", "city_relation"]),
            models.Index(fields=["mosque_name", "mobile_number", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.mosque_name} ({self.mobile_number})"

    def save(self, *args, **kwargs):
        if self.city_relation_id:
            from apps.locations.models import City
            city_obj = City.objects.filter(id=self.city_relation_id).first()
            if city_obj:
                self.city = city_obj.name
                if not self.city_raw:
                    self.city_raw = city_obj.name
        elif self.city:
            if not self.city_raw:
                self.city_raw = self.city
            from apps.locations.models import City
            import string
            normalized = " ".join(self.city.split()).strip(string.punctuation).lower()
            city_obj = City.objects.filter(name__iexact=normalized).first()
            if not city_obj:
                city_obj = City.objects.filter(name__icontains=normalized).first()
            if city_obj:
                self.city_relation = city_obj
                self.city = city_obj.name
                
        super().save(*args, **kwargs)


class MosqueOperatingSchedule(TimeStampedModel):
    """Operating schedule configuration for a Mosque."""

    mosque = models.OneToOneField(
        Mosque,
        on_delete=models.CASCADE,
        related_name="operating_schedule",
    )
    open_24_hours = models.BooleanField(default=False)

    fajr_open = models.TimeField(null=True, blank=True)
    fajr_close = models.TimeField(null=True, blank=True)

    dhuhr_open = models.TimeField(null=True, blank=True)
    dhuhr_close = models.TimeField(null=True, blank=True)

    asr_open = models.TimeField(null=True, blank=True)
    asr_close = models.TimeField(null=True, blank=True)

    maghrib_open = models.TimeField(null=True, blank=True)
    maghrib_close = models.TimeField(null=True, blank=True)

    isha_open = models.TimeField(null=True, blank=True)
    isha_close = models.TimeField(null=True, blank=True)

    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_operating_schedules",
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Schedule for {self.mosque.mosque_name}"

    def get_current_status(self) -> dict:
        """Calculate the current open/closed status using local timezone time."""
        if self.open_24_hours:
            return {
                "is_open": True,
                "opens_at": None,
                "closes_at": None,
            }

        # Check if any window is configured
        windows = [
            ("fajr", self.fajr_open, self.fajr_close),
            ("dhuhr", self.dhuhr_open, self.dhuhr_close),
            ("asr", self.asr_open, self.asr_close),
            ("maghrib", self.maghrib_open, self.maghrib_close),
            ("isha", self.isha_open, self.isha_close),
        ]

        valid_windows = []
        for name, open_t, close_t in windows:
            if open_t is not None and close_t is not None:
                valid_windows.append((name, open_t, close_t))

        if not valid_windows:
            return {
                "is_open": False,
                "opens_at": None,
                "closes_at": None,
                "message": "No operating schedule configured yet.",
            }

        import django.utils.timezone as django_timezone
        from zoneinfo import ZoneInfo
        from apps.mosques.services import MosqueAvailabilityEngine

        city_ref = self.mosque.city_relation if self.mosque.city_relation else self.mosque.city
        tz_name = MosqueAvailabilityEngine.get_city_timezone(city_ref)

        now = django_timezone.now().astimezone(ZoneInfo(tz_name))
        current_time = now.time()

        # Check if we are inside any window
        for name, open_t, close_t in valid_windows:
            if open_t <= close_t:
                if open_t <= current_time <= close_t:
                    return {
                        "is_open": True,
                        "opens_at": None,
                        "closes_at": close_t.strftime("%I:%M %p"),
                    }
            else:
                if current_time >= open_t or current_time <= close_t:
                    return {
                        "is_open": True,
                        "opens_at": None,
                        "closes_at": close_t.strftime("%I:%M %p"),
                    }

        # Closed: Find next open time
        valid_windows.sort(key=lambda x: x[1])
        next_open = None
        for name, open_t, close_t in valid_windows:
            if open_t > current_time:
                next_open = open_t
                break

        if next_open is None:
            next_open = valid_windows[0][1]

        return {
            "is_open": False,
            "opens_at": next_open.strftime("%I:%M %p"),
            "closes_at": None,
        }


class MosquePhoto(TimeStampedModel):
    """Photo gallery entry for a Mosque."""

    mosque = models.ForeignKey(
        Mosque,
        on_delete=models.CASCADE,
        related_name="photos",
    )
    image = models.ImageField(upload_to="mosque_photos/", storage=default_storage)
    title = models.CharField(max_length=255, blank=True)
    caption = models.TextField(blank=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_photos",
    )

    class Meta:
        ordering = ["display_order", "created_at"]

    def __str__(self) -> str:
        return f"{self.title or 'Photo'} for {self.mosque.mosque_name}"


class MosqueAnnouncement(TimeStampedModel):
    """Operational announcement / notice board entry for a Mosque."""

    class Priority(models.TextChoices):
        NORMAL = "normal", "Normal"
        IMPORTANT = "important", "Important"
        URGENT = "urgent", "Urgent"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    mosque = models.ForeignKey(
        Mosque,
        on_delete=models.CASCADE,
        related_name="announcements",
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_announcements",
    )

    class Meta:
        ordering = ["-priority", "-created_at"]
        indexes = [
            models.Index(fields=["is_active", "status", "start_date", "end_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.priority}) - {self.mosque.mosque_name}"


class MosqueEvent(TimeStampedModel):
    """Upcoming event or activity scheduled at a Mosque."""

    class EventType(models.TextChoices):
        LECTURE = "lecture", "Lecture"
        DARS = "dars", "Dars (Study Circle)"
        YOUTH_PROGRAM = "youth_program", "Youth Program"
        COMMUNITY_MEETING = "community_meeting", "Community Meeting"
        FUNDRAISER = "fundraiser", "Fundraiser"
        RAMADAN = "ramadan", "Ramadan Program"
        EID = "eid", "Eid Event"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    mosque = models.ForeignKey(
        Mosque,
        on_delete=models.CASCADE,
        related_name="events",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        default=EventType.OTHER,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    event_date = models.DateField()
    event_time = models.TimeField()
    event_location = models.CharField(max_length=255, blank=True)
    speaker_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_events",
    )

    class Meta:
        ordering = ["event_date", "event_time"]
        indexes = [
            models.Index(fields=["is_active", "status", "event_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} on {self.event_date} - {self.mosque.mosque_name}"


class CommunitySchedule(TimeStampedModel):
    """Schedules representing timetables (Weekly Dars, Jumuah sermon slots, etc.)."""

    class ScheduleType(models.TextChoices):
        KHUTBAH = "khutbah", "Friday Khutbah Shift"
        WEEKLY_DARS = "weekly_dars", "Weekly Dars"

    mosque = models.ForeignKey(
        Mosque,
        on_delete=models.CASCADE,
        related_name="schedules",
    )
    schedule_type = models.CharField(
        max_length=50,
        choices=ScheduleType.choices,
        db_index=True,
    )
    event_date = models.DateField(db_index=True)
    start_time = models.TimeField()
    speaker = models.CharField(max_length=255)
    topic = models.CharField(max_length=255, blank=True)
    extended_data = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["event_date", "start_time"]
        indexes = [
            models.Index(fields=["mosque", "schedule_type", "event_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_schedule_type_display()} on {self.event_date} by {self.speaker}"
