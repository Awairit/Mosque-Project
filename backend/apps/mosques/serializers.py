"""Serializers for mosque-related APIs."""

from rest_framework import serializers

from django.utils import timezone
from apps.common.utils.geo import calculate_haversine
from apps.mosques.models import (
    Mosque,
    MosqueRegistrationRequest,
    MosqueOperatingSchedule,
    MosquePhoto,
    MosqueAnnouncement,
    MosqueEvent,
    CommunitySchedule,
)
from apps.mosques.services import MosqueAvailabilityEngine
from apps.prayers.serializers import PrayerTimingSerializer


class MosquePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MosquePhoto
        fields = (
            "id",
            "image",
            "title",
            "caption",
            "display_order",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class MosqueAnnouncementSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    mosque_name = serializers.CharField(source="mosque.mosque_name", read_only=True)

    class Meta:
        model = MosqueAnnouncement
        fields = (
            "id",
            "mosque",
            "mosque_name",
            "city",
            "city_name",
            "title",
            "short_summary",
            "content",
            "banner_image",
            "announcement_type",
            "priority",
            "status",
            "start_date",
            "end_date",
            "publish_date",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class MosqueEventSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    mosque_name = serializers.CharField(source="mosque.mosque_name", read_only=True)

    class Meta:
        model = MosqueEvent
        fields = (
            "id",
            "mosque",
            "mosque_name",
            "city",
            "city_name",
            "title",
            "description",
            "event_type",
            "status",
            "event_date",
            "event_time",
            "end_time",
            "event_location",
            "speaker_name",
            "registration_required",
            "max_capacity",
            "banner",
            "attachments",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class MosqueListSerializer(serializers.ModelSerializer):
    prayer_timing = serializers.SerializerMethodField()
    operating_status = serializers.SerializerMethodField()
    distance = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    city_id = serializers.SerializerMethodField()

    class Meta:
        model = Mosque
        fields = (
            "id",
            "mosque_name",
            "city",
            "city_id",
            "address",
            "latitude",
            "longitude",
            "google_maps_url",
            "women_prayer_available",
            "mosque_status",
            "description",
            "contact_phone",
            "contact_email",
            "website",
            "imam_name",
            "imam_contact_number",
            # Core facilities
            "parking_available",
            "wudu_facility_available",
            "wheelchair_accessible",
            # Extended facilities
            "drinking_water_available",
            "washrooms_available",
            "library_available",
            "quran_classes_available",
            "hifz_program_available",
            "nikah_service_available",
            "muslim_burial_ground_available",
            "community_hall_available",
            "ramadan_iftar_available",
            "eid_prayer_ground_available",
            "zakat_collection_available",
            "funeral_prayer_facility_available",
            "mosque_type",
            "separate_women_entrance",
            "prayer_timing",
            "operating_status",
            "distance",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields

    def get_city(self, obj) -> str:
        if obj.city_relation:
            return obj.city_relation.name
        return obj.city or ""

    def get_city_id(self, obj) -> int | None:
        return obj.city_relation_id

    def get_operating_status(self, obj) -> dict:
        engine = MosqueAvailabilityEngine(obj)
        return engine.get_availability()

    def get_prayer_timing(self, obj) -> dict | None:
        from apps.prayers.services import CongregationTimingResolver
        from apps.prayers.serializers import ResolvedPrayerTimingSerializer
        from apps.prayers.models import PrayerTiming
        from zoneinfo import ZoneInfo
        from django.utils import timezone
        
        try:
            timing = obj.prayer_timing
        except PrayerTiming.DoesNotExist:
            return None
            
        date_val = self.context.get("date")
        if not date_val:
            city = obj.city_relation
            tz_name = city.timezone if (city and city.timezone) else "Asia/Kolkata"
            date_val = timezone.now().astimezone(ZoneInfo(tz_name)).date()
            
        resolved = CongregationTimingResolver.resolve_prayer_timing(timing, date_val)
        if not resolved:
            return None

        # Build a plain dict from the resolved dataclass, then add the ORM-level
        # timestamp (already in memory via select_related — no extra DB query).
        # We serialise via ResolvedPrayerTimingSerializer so field formatting
        # (time format strings, date format, etc.) stays in one place.
        payload = {
            "fajr_time": resolved.fajr_time,
            "dhuhr_time": resolved.dhuhr_time,
            "asr_time": resolved.asr_time,
            "maghrib_time": resolved.maghrib_time,
            "isha_time": resolved.isha_time,
            "jumuah_time": resolved.jumuah_time,
            "effective_from": resolved.effective_from,
            "maghrib_congregation_mode": resolved.maghrib_congregation_mode,
            "updated_at": timing.updated_at if timing.updated_at else None,
        }
        return ResolvedPrayerTimingSerializer(payload).data


    def get_distance(self, obj) -> float | None:
        if hasattr(obj, "distance_val") and obj.distance_val is not None:
            return obj.distance_val

        user_lat = self.context.get("lat")
        user_lon = self.context.get("lon")
        if user_lat is not None and user_lon is not None and obj.latitude is not None and obj.longitude is not None:
            try:
                return calculate_haversine(user_lat, user_lon, obj.latitude, obj.longitude)
            except (ValueError, TypeError):
                pass
        return None


class MosqueDetailSerializer(MosqueListSerializer):
    photos = serializers.SerializerMethodField()
    announcements = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()
    schedules = serializers.SerializerMethodField()
    janazah_notices = serializers.SerializerMethodField()

    class Meta(MosqueListSerializer.Meta):
        fields = MosqueListSerializer.Meta.fields + (
            "photos",
            "announcements",
            "events",
            "schedules",
            "janazah_notices",
        )
        read_only_fields = fields

    def get_photos(self, obj):
        if hasattr(obj, "_prefetched_objects_cache") and "photos" in obj._prefetched_objects_cache:
            photos = obj.photos.all()
        else:
            photos = obj.photos.filter(is_active=True).order_by("display_order")
        return MosquePhotoSerializer(photos, many=True, context=self.context).data

    def get_announcements(self, obj):
        if hasattr(obj, "_prefetched_objects_cache") and "announcements" in obj._prefetched_objects_cache:
            announcements = obj.announcements.all()
        else:
            today = timezone.localdate()
            announcements = obj.announcements.filter(
                is_active=True,
                status="published",
                start_date__lte=today,
                end_date__gte=today,
            ).order_by("-created_at")
        return MosqueAnnouncementSerializer(announcements, many=True, context=self.context).data

    def get_events(self, obj):
        if hasattr(obj, "_prefetched_objects_cache") and "events" in obj._prefetched_objects_cache:
            events = obj.events.all()
        else:
            today = timezone.localdate()
            events = obj.events.filter(
                is_active=True,
                status="published",
                event_date__gte=today,
            ).order_by("event_date", "event_time")
        return MosqueEventSerializer(events, many=True, context=self.context).data

    def get_schedules(self, obj):
        if hasattr(obj, "_prefetched_objects_cache") and "schedules" in obj._prefetched_objects_cache:
            schedules = obj.schedules.all()
        else:
            today = timezone.localdate()
            schedules = obj.schedules.filter(
                event_date__gte=today
            ).order_by("event_date", "start_time")
        return CommunityScheduleSerializer(schedules, many=True, context=self.context).data

    def get_janazah_notices(self, obj):
        from apps.community_services.serializers import JanazahNoticeSerializer
        if hasattr(obj, "_prefetched_objects_cache") and "janazah_notices" in obj._prefetched_objects_cache:
            notices = obj.janazah_notices.all()
        else:
            notices = obj.janazah_notices.filter(status="published")
        return JanazahNoticeSerializer(notices, many=True, context=self.context).data


# Alias for backward compatibility with existing tests and scripts
MosqueSerializer = MosqueDetailSerializer




class MosqueRegistrationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = MosqueRegistrationRequest
        fields = (
            "id",
            "mosque_name",
            "admin_name",
            "mobile_number",
            "email",
            "imam_name",
            "city",
            "address",
            "google_maps_link",
            "google_maps_url",
            "women_prayer_available",
            "notes",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "status", "created_at", "updated_at")

    def validate_mosque_name(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Mosque name is required.")
        return value

    def validate_mobile_number(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Mobile number is required.")
            
        from apps.common.utils.strings import normalize_phone_number
        try:
            normalized = normalize_phone_number(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))
            
        from django.contrib.auth.models import User
        from django.db.models import Q
        local_digits = normalized.replace("+91", "")
        existing_user = User.objects.filter(
            Q(username=normalized) | Q(username=local_digits)
        ).first()
        if existing_user and hasattr(existing_user, 'mosque_admin'):
            raise serializers.ValidationError("This phone number is already registered.")
            
        return normalized

    def validate_email(self, value: str) -> str:
        value = value.strip() if value else ""
        if value:
            from django.contrib.auth.models import User
            existing_user = User.objects.filter(email=value).exclude(email="").first()
            if existing_user and hasattr(existing_user, 'mosque_admin'):
                raise serializers.ValidationError("This email address is already registered.")
        return value

    def validate(self, attrs):
        mosque_name = attrs.get("mosque_name", "").strip()
        mobile_number = attrs.get("mobile_number", "").strip()

        # Synchronize google_maps_link and google_maps_url for compatibility
        link = attrs.get("google_maps_link")
        url = attrs.get("google_maps_url")
        if link and not url:
            attrs["google_maps_url"] = link
        elif url and not link:
            attrs["google_maps_link"] = url

        duplicate_exists = MosqueRegistrationRequest.objects.filter(
            mosque_name__iexact=mosque_name,
            mobile_number=mobile_number,
            status=MosqueRegistrationRequest.Status.PENDING,
        ).exists()

        if duplicate_exists:
            raise serializers.ValidationError(
                {
                    "non_field_errors": [
                        "A pending registration request already exists for this mosque and mobile number."
                    ]
                }
            )

        return attrs


class MosqueProfileSerializer(serializers.ModelSerializer):
    city_id = serializers.IntegerField(source="city_relation_id", required=False, allow_null=True)

    class Meta:
        model = Mosque
        fields = (
            "id",
            "mosque_name",
            "city",
            "city_id",
            "address",
            "description",
            "contact_phone",
            "contact_email",
            "website",
            "imam_name",
            "imam_contact_number",
            "women_prayer_available",
            # Core facilities
            "parking_available",
            "wudu_facility_available",
            "wheelchair_accessible",
            # Extended facilities
            "drinking_water_available",
            "washrooms_available",
            "library_available",
            "quran_classes_available",
            "hifz_program_available",
            "nikah_service_available",
            "muslim_burial_ground_available",
            "community_hall_available",
            "ramadan_iftar_available",
            "eid_prayer_ground_available",
            "zakat_collection_available",
            "funeral_prayer_facility_available",
            "mosque_type",
            "separate_women_entrance",
            "profile_image",
            "mosque_status",
        )
        read_only_fields = ("id", "profile_image", "mosque_status")

    def validate(self, attrs):
        from apps.locations.models import City
        
        if "city_relation_id" in attrs:
            city_relation_id = attrs.get("city_relation_id")
            if city_relation_id is not None:
                try:
                    city_obj = City.objects.get(id=city_relation_id)
                    attrs["city"] = city_obj.name
                except City.DoesNotExist:
                    raise serializers.ValidationError({"city_id": "City with this ID does not exist."})
            else:
                attrs["city"] = ""
        elif "city" in attrs:
            city_name = attrs.get("city")
            if city_name:
                import string
                normalized = " ".join(city_name.split()).strip(string.punctuation).lower()
                city_obj = City.objects.filter(name__iexact=normalized).first()
                if not city_obj:
                    city_obj = City.objects.filter(name__icontains=normalized).first()
                if city_obj:
                    attrs["city_relation"] = city_obj
                    attrs["city"] = city_obj.name
            else:
                attrs["city_relation"] = None
                
        return attrs


class MosqueOperatingScheduleSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.ReadOnlyField(source="updated_by.username")

    class Meta:
        model = MosqueOperatingSchedule
        fields = (
            "id",
            "mosque",
            "open_24_hours",
            "fajr_open",
            "fajr_close",
            "dhuhr_open",
            "dhuhr_close",
            "asr_open",
            "asr_close",
            "maghrib_open",
            "maghrib_close",
            "isha_open",
            "isha_close",
            "updated_by",
            "updated_by_username",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "mosque",
            "updated_by",
            "updated_by_username",
            "created_at",
            "updated_at",
        )


class CommunityScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunitySchedule
        fields = (
            "id",
            "mosque",
            "schedule_type",
            "event_date",
            "start_time",
            "speaker",
            "topic",
            "extended_data",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "mosque", "created_at", "updated_at")

    def validate(self, attrs):
        request = self.context.get("request")
        if request and hasattr(request.user, "mosque_admin"):
            mosque = request.user.mosque_admin.mosque
        else:
            mosque = self.context.get("mosque")

        if not mosque and self.instance:
            mosque = self.instance.mosque

        schedule_type = attrs.get("schedule_type", self.instance.schedule_type if self.instance else None)
        event_date = attrs.get("event_date", self.instance.event_date if self.instance else None)
        extended_data = attrs.get("extended_data", self.instance.extended_data if self.instance else {})

        if schedule_type == "khutbah" and event_date:
            shift_number = extended_data.get("shift_number")
            if shift_number is not None:
                qs = CommunitySchedule.objects.filter(
                    mosque=mosque,
                    schedule_type="khutbah",
                    event_date=event_date,
                    extended_data__shift_number=int(shift_number)
                )
                if self.instance:
                    qs = qs.exclude(id=self.instance.id)
                if qs.exists():
                    raise serializers.ValidationError(
                        {"non_field_errors": [f"A Jumuah Khutbah schedule already exists for shift {shift_number} on {event_date}."]}
                    )
        return attrs

