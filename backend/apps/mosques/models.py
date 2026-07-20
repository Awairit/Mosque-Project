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
    contact_email = models.CharField(max_length=254, blank=True)
    website = models.URLField(max_length=255, blank=True)

    # Imam Information
    imam_name = models.CharField(max_length=255, blank=True)
    imam_contact_number = models.CharField(max_length=32, blank=True)

    # Core Facilities (existing)
    parking_available = models.BooleanField(default=False)
    wudu_facility_available = models.BooleanField(default=False)
    wheelchair_accessible = models.BooleanField(default=False)
    profile_image = models.ImageField(
        upload_to="mosque_profiles/", null=True, blank=True
    )

    # Extended Facilities
    drinking_water_available = models.BooleanField(default=False)
    washrooms_available = models.BooleanField(default=False)
    library_available = models.BooleanField(default=False)
    quran_classes_available = models.BooleanField(default=False)
    hifz_program_available = models.BooleanField(default=False)
    nikah_service_available = models.BooleanField(default=False)
    muslim_burial_ground_available = models.BooleanField(default=False)
    community_hall_available = models.BooleanField(default=False)
    ramadan_iftar_available = models.BooleanField(default=False)
    eid_prayer_ground_available = models.BooleanField(default=False)
    zakat_collection_available = models.BooleanField(default=False)
    funeral_prayer_facility_available = models.BooleanField(default=False)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track original URL so save() can detect changes.
        self._original_google_maps_url = self.google_maps_url

    def save(self, *args, **kwargs):
        from apps.mosques.services import extract_coordinates_from_url

        url_changed = self.google_maps_url != self._original_google_maps_url
        coords_missing = self.latitude is None or self.longitude is None

        # Re-extract coordinates when:
        #   (a) URL was newly supplied and coords are missing, OR
        #   (b) URL changed (re-sync regardless of existing coords).
        # Never touch coords when the URL is empty or unchanged with valid coords.
        if self.google_maps_url and (coords_missing or url_changed):
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
        DRAFT = "draft", "Draft"
        WHATSAPP_VERIFIED = "whatsapp_verified", "WhatsApp Verified"
        PENDING = "pending", "Pending Review"
        UNDER_VERIFICATION = "under_verification", "Under Verification"
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

    # Contact & Imam Information
    email = models.CharField(max_length=254, blank=True)
    imam_name = models.CharField(max_length=255, blank=True)

    # WhatsApp / Mobile Verification
    mobile_verified = models.BooleanField(default=False)
    whatsapp_verified = models.BooleanField(default=False)
    whatsapp_verified_at = models.DateTimeField(null=True, blank=True)
    verification_method = models.CharField(max_length=50, blank=True)
    verification_timestamp = models.DateTimeField(null=True, blank=True)

    # Super Admin Workflow
    under_verification_at = models.DateTimeField(null=True, blank=True)
    under_verification_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="under_verification_requests",
    )
    super_admin_notes = models.TextField(
        blank=True,
        help_text="Internal verification notes. Never visible publicly. E.g. 'Verified via WhatsApp call.'",
    )

    status = models.CharField(
        max_length=25,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_requests",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rejected_requests",
    )
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

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
    """Operational announcement / notice board entry for a Mosque or City."""

    class Priority(models.TextChoices):
        NORMAL = "normal", "Normal"
        IMPORTANT = "important", "Important"
        URGENT = "urgent", "Urgent"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    class AnnouncementType(models.TextChoices):
        GENERAL = "general", "General"
        RAMADAN = "ramadan", "Ramadan"
        EID = "eid", "Eid"
        PRAYER_CHANGE = "prayer_change", "Prayer Change"
        EMERGENCY = "emergency", "Emergency"
        WEATHER = "weather", "Weather"
        COMMUNITY = "community", "Community"
        CHARITY = "charity", "Charity"
        EDUCATION = "education", "Education"
        LOST_FOUND = "lost_found", "Lost & Found"

    mosque = models.ForeignKey(
        Mosque,
        on_delete=models.CASCADE,
        related_name="announcements",
        null=True,
        blank=True,
    )
    city = models.ForeignKey(
        "locations.City",
        on_delete=models.CASCADE,
        related_name="announcements",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    short_summary = models.CharField(max_length=255, blank=True)
    content = models.TextField() # Full Description
    banner_image = models.CharField(max_length=500, blank=True)
    announcement_type = models.CharField(
        max_length=50,
        choices=AnnouncementType.choices,
        default=AnnouncementType.GENERAL,
    )
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
    publish_date = models.DateField(null=True, blank=True)
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
        target = self.mosque.mosque_name if self.mosque else (self.city.name if self.city else "Global")
        return f"{self.title} ({self.priority}) - {target}"


class MosqueEvent(TimeStampedModel):
    """Upcoming event or activity scheduled at a Mosque or City."""

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
        null=True,
        blank=True,
    )
    city = models.ForeignKey(
        "locations.City",
        on_delete=models.CASCADE,
        related_name="events",
        null=True,
        blank=True,
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
    event_time = models.TimeField() # Start Time
    end_time = models.TimeField(null=True, blank=True)
    event_location = models.CharField(max_length=255, blank=True)
    speaker_name = models.CharField(max_length=255, blank=True)
    registration_required = models.BooleanField(default=False)
    max_capacity = models.IntegerField(null=True, blank=True)
    banner = models.CharField(max_length=500, blank=True)
    attachments = models.JSONField(null=True, blank=True)
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
        target = self.mosque.mosque_name if self.mosque else (self.city.name if self.city else "Global")
        return f"{self.title} on {self.event_date} - {target}"


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


class NotificationJob(TimeStampedModel):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    recipient = models.CharField(max_length=255)
    channel = models.CharField(max_length=50) # e.g. whatsapp, sms, email, push, in_app
    title = models.CharField(max_length=255, blank=True)
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-priority", "-created_at"]

    def __str__(self) -> str:
        return f"{self.channel} job for {self.recipient} - status: {self.status}"


from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=MosqueAnnouncement)
def handle_announcement_published(sender, instance, created, **kwargs):
    if instance.status == "published" and instance.is_active:
        priority = NotificationJob.Priority.HIGH if instance.announcement_type == "emergency" else NotificationJob.Priority.NORMAL
        recipient = "+919999999999"
        message = f"Announcement: {instance.title} - {instance.short_summary or instance.content[:100]}"
        
        if not NotificationJob.objects.filter(
            recipient=recipient,
            title=instance.title,
            channel="whatsapp"
        ).exists():
            job = NotificationJob.objects.create(
                recipient=recipient,
                channel="whatsapp",
                title=instance.title,
                message=message,
                priority=priority,
                status=NotificationJob.Status.PENDING
            )
            from apps.common.services.notification import notification_service
            success = notification_service.send_whatsapp(recipient, message)
            if success:
                job.status = NotificationJob.Status.SENT
            else:
                job.status = NotificationJob.Status.FAILED
                job.error_message = "Failed to dispatch via notification_service."
            job.save()


@receiver(post_save, sender=MosqueEvent)
def handle_event_published(sender, instance, created, **kwargs):
    if instance.status == "published" and instance.is_active:
        priority = NotificationJob.Priority.NORMAL
        recipient = "+919999999999"
        message = f"New Event: {instance.title} scheduled on {instance.event_date} at {instance.event_time}"
        
        if not NotificationJob.objects.filter(
            recipient=recipient,
            title=instance.title,
            channel="whatsapp"
        ).exists():
            job = NotificationJob.objects.create(
                recipient=recipient,
                channel="whatsapp",
                title=instance.title,
                message=message,
                priority=priority,
                status=NotificationJob.Status.PENDING
            )
            from apps.common.services.notification import notification_service
            success = notification_service.send_whatsapp(recipient, message)
            if success:
                job.status = NotificationJob.Status.SENT
            else:
                job.status = NotificationJob.Status.FAILED
                job.error_message = "Failed to dispatch via notification_service."
            job.save()
