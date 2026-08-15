from django.contrib import admin
from django.contrib.auth.models import User
from django import forms
from django.core.exceptions import ValidationError
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


class MosqueAdminForm(forms.ModelForm):
    """Admin form for Mosque that validates Google Maps URL coordinate extraction.

    Prevents saving a mosque that has a Google Maps URL but unresolvable
    coordinates, which was the root cause of the V1.1 production distance
    calculation failures.
    """

    class Meta:
        model = Mosque
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        url = cleaned_data.get("google_maps_url") or ""
        lat = cleaned_data.get("latitude")
        lon = cleaned_data.get("longitude")

        # Only validate if a URL is supplied AND both lat/lon are absent.
        # If the admin has manually entered coordinates, trust them.
        if url and (lat is None or lon is None):
            from apps.mosques.services import extract_coordinates_from_url
            extracted_lat, extracted_lon = extract_coordinates_from_url(url)
            if extracted_lat is None or extracted_lon is None:
                raise ValidationError(
                    "Unable to extract coordinates from the supplied Google Maps URL. "
                    "Please provide a valid Google Maps location URL, or enter the "
                    "latitude and longitude manually."
                )
            # Populate the form fields so they are saved correctly.
            cleaned_data["latitude"] = extracted_lat
            cleaned_data["longitude"] = extracted_lon

        return cleaned_data


@admin.register(Mosque)
class MosqueAdmin(admin.ModelAdmin):
    form = MosqueAdminForm
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
                    "google_maps_url",
                    "latitude",
                    "longitude",
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.status == MosqueRegistrationRequest.Status.APPROVED:
            from apps.mosques.services import approve_mosque_registration_request
            user = request.user if request and hasattr(request, "user") else None
            approve_mosque_registration_request(obj, approved_by_user=user)

    @admin.action(description="Approve selected requests")
    def approve_selected_requests(self, request, queryset):
        from apps.mosques.services import approve_mosque_registration_request
        from django.contrib.auth.models import User
        approved_count = 0
        user = request.user if request and hasattr(request, "user") and isinstance(request.user, User) else None

        for registration_request in queryset:
            result = approve_mosque_registration_request(registration_request, approved_by_user=user)
            mosque = result["mosque"]
            if mosque.google_maps_url and (mosque.latitude is None or mosque.longitude is None):
                if request and hasattr(self, "message_user"):
                    self.message_user(
                        request,
                        f"Warning: Could not extract coordinates from URL for '{mosque.mosque_name}'. Please verify the URL or enter coordinates manually.",
                        level="warning"
                    )
            approved_count += 1

        if request and hasattr(self, "message_user"):
            self.message_user(
                request,
                f"Approved {approved_count} request(s) and materialized corresponding Mosque and MosqueAdmin records.",
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
