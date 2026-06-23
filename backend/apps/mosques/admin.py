"""Django admin registrations for mosque workflows."""

from django.contrib import admin
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.crypto import get_random_string

from apps.accounts.models import MosqueAdmin as AccountsMosqueAdmin
from apps.mosques.models import (
    Mosque,
    MosqueRegistrationRequest,
    MosqueOperatingSchedule,
    MosquePhoto,
    MosqueAnnouncement,
    MosqueEvent,
)


@admin.register(Mosque)
class MosqueAdmin(admin.ModelAdmin):
    autocomplete_fields = ["city_relation"]
    list_display = (
        "mosque_name",
        "city",
        "city_relation",
        "mosque_type",
        "mosque_status",
        "women_prayer_available",
        "parking_available",
        "wudu_facility_available",
        "wheelchair_accessible",
        "created_at",
    )
    list_filter = (
        "mosque_status",
        "mosque_type",
        "city",
        "city_relation",
        "women_prayer_available",
        "parking_available",
        "wudu_facility_available",
        "wheelchair_accessible",
    )
    search_fields = ("mosque_name", "city", "city_relation__name", "address", "description")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("mosque_name",)
    fieldsets = (
        (
            "Basic Info",
            {
                "fields": (
                    "mosque_name",
                    "mosque_type",
                    "mosque_status",
                    "description",
                    "contact_phone",
                    "website",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "city",
                    "city_relation",
                    "address",
                    "google_maps_url",
                    "latitude",
                    "longitude",
                )
            },
        ),
        (
            "Facilities",
            {
                "fields": (
                    "women_prayer_available",
                    "separate_women_entrance",
                    "parking_available",
                    "wudu_facility_available",
                    "wheelchair_accessible",
                    "profile_image",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )


@admin.register(MosqueOperatingSchedule)
class MosqueOperatingScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "mosque",
        "open_24_hours",
        "updated_by",
        "updated_at",
    )
    list_filter = ("open_24_hours", "updated_at")
    search_fields = ("mosque__mosque_name", "updated_by__username")
    readonly_fields = ("created_at", "updated_at")


@admin.register(MosqueRegistrationRequest)
class MosqueRegistrationRequestAdmin(admin.ModelAdmin):
    autocomplete_fields = ["city_relation"]
    list_display = (
        "mosque_name",
        "admin_name",
        "mobile_number",
        "city",
        "city_raw",
        "city_relation",
        "women_prayer_available",
        "status",
        "created_at",
    )
    list_filter = ("status", "city_relation", "created_at")
    search_fields = ("mosque_name", "admin_name", "mobile_number", "city", "city_raw", "city_relation__name", "address")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    actions = ("approve_selected_requests", "reject_selected_requests")

    fieldsets = (
        (
            "Request Details",
            {
                "fields": (
                    "mosque_name",
                    "admin_name",
                    "mobile_number",
                    "city",
                    "city_raw",
                    "city_relation",
                    "address",
                    "google_maps_link",
                    "women_prayer_available",
                    "notes",
                )
            },
        ),
        (
            "Review",
            {
                "fields": ("status",),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )

    @admin.action(description="Approve selected requests")
    def approve_selected_requests(self, request, queryset):
        created_count = 0
        approved_count = 0

        for registration_request in queryset:
            # Copy google_maps_url from request
            req_url = registration_request.google_maps_url or registration_request.google_maps_link

            # 1. Idempotently get or create the Mosque
            mosque_qs = Mosque.objects.filter(
                mosque_name__iexact=registration_request.mosque_name,
                address__iexact=registration_request.address,
            )
            if registration_request.city_relation:
                mosque = mosque_qs.filter(city_relation=registration_request.city_relation).first()
            else:
                mosque = mosque_qs.filter(city__iexact=registration_request.city).first()

            if not mosque:
                mosque = Mosque.objects.create(
                    mosque_name=registration_request.mosque_name,
                    city=registration_request.city,
                    city_relation=registration_request.city_relation,
                    address=registration_request.address,
                    google_maps_url=req_url,
                    women_prayer_available=registration_request.women_prayer_available,
                    mosque_status=Mosque.MosqueStatus.ACTIVE,
                )
                created_count += 1
            else:
                if req_url:
                    mosque.google_maps_url = req_url
            
            # Resolve coordinates from Google Maps URL
            if mosque.google_maps_url and (mosque.latitude is None or mosque.longitude is None):
                from apps.mosques.services import extract_coordinates_from_url
                lat, lon = extract_coordinates_from_url(mosque.google_maps_url)
                if lat is not None and lon is not None:
                    mosque.latitude = lat
                    mosque.longitude = lon
                else:
                    if request:
                        self.message_user(
                            request,
                            f"Warning: Could not extract coordinates from URL for '{mosque.mosque_name}'. Please verify the URL or enter coordinates manually.",
                            level="warning"
                        )
            
            mosque.save()

            # 2. Idempotently create MosqueAdmin and User
            admin_profile = AccountsMosqueAdmin.objects.filter(
                mobile_number=registration_request.mobile_number
            ).first()

            if not admin_profile:
                user = User.objects.filter(username=registration_request.mobile_number).first()
                temp_password = None
                if not user:
                    temp_password = get_random_string(length=12)
                    user = User.objects.create_user(
                        username=registration_request.mobile_number,
                        password=temp_password,
                    )

                admin_profile = AccountsMosqueAdmin.objects.create(
                    user=user,
                    mosque=mosque,
                    mobile_number=registration_request.mobile_number,
                    is_active=True,
                )

                if temp_password and request:
                    self.message_user(
                        request,
                        (
                            f"Created admin account for '{mosque.mosque_name}'. "
                            f"Username/Phone: {registration_request.mobile_number}, "
                            f"Temporary Password: {temp_password}"
                        ),
                        level="info",
                    )

            if registration_request.status != MosqueRegistrationRequest.Status.APPROVED:
                registration_request.status = MosqueRegistrationRequest.Status.APPROVED
                registration_request.save(update_fields=["status", "updated_at"])
                approved_count += 1

        if request:
            self.message_user(
                request,
                f"Approved {approved_count} request(s). Created {created_count} mosque record(s).",
            )

    @admin.action(description="Reject selected requests")
    def reject_selected_requests(self, request, queryset):
        updated_count = queryset.exclude(
            status=MosqueRegistrationRequest.Status.REJECTED
        ).update(
            status=MosqueRegistrationRequest.Status.REJECTED,
            updated_at=timezone.now(),
        )

        if request:
            self.message_user(request, f"Rejected {updated_count} request(s).")


@admin.register(MosquePhoto)
class MosquePhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "mosque", "title", "display_order", "is_active", "uploaded_by")
    list_filter = ("is_active", "mosque")
    search_fields = ("title", "caption", "mosque__mosque_name")


@admin.register(MosqueAnnouncement)
class MosqueAnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "mosque", "priority", "status", "start_date", "end_date", "is_active")
    list_filter = ("priority", "status", "is_active", "mosque")
    search_fields = ("title", "content", "mosque__mosque_name")


@admin.register(MosqueEvent)
class MosqueEventAdmin(admin.ModelAdmin):
    list_display = ("title", "mosque", "event_type", "status", "event_date", "event_time", "is_active")
    list_filter = ("event_type", "status", "is_active", "mosque")
    search_fields = ("title", "description", "speaker_name", "mosque__mosque_name")
