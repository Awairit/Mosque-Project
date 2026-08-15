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
    published_by = serializers.SerializerMethodField()

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
            "published_by",
        )
        read_only_fields = ("id", "created_at", "updated_at", "published_by")

    def get_published_by(self, obj) -> dict | None:
        # Mosque-scoped content must not receive City Admin attribution
        if obj.mosque_id is not None:
            return None

        user = obj.created_by
        city_admin = None
        if user and hasattr(user, "city_admin") and user.city_admin.is_active:
            city_admin = user.city_admin
        elif obj.city:
            from apps.accounts.models import CityAdmin
            city_admin = CityAdmin.objects.filter(city=obj.city, is_active=True).select_related("user").first()

        if not city_admin and not (user and hasattr(user, "city_admin")):
            return None

        ca_user = city_admin.user if city_admin else user
        full_name = f"{ca_user.first_name} {ca_user.last_name}".strip()
        if not full_name:
            full_name = ca_user.username

        city_name = obj.city.name if obj.city else (city_admin.city.name if city_admin and city_admin.city else "")

        return {
            "name": full_name,
            "role": "City Administrator",
            "city": city_name,
        }


class MosqueEventSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source="city.name", read_only=True)
    mosque_name = serializers.CharField(source="mosque.mosque_name", read_only=True)
    published_by = serializers.SerializerMethodField()
    temporal_status = serializers.SerializerMethodField()
    organizer_name = serializers.SerializerMethodField()

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
            "published_by",
            "temporal_status",
            "organizer_name",
        )
        read_only_fields = ("id", "created_at", "updated_at", "published_by", "temporal_status", "organizer_name")

    def get_temporal_status(self, obj) -> str:
        from django.utils import timezone
        from zoneinfo import ZoneInfo
        tz_name = obj.city.timezone if (obj.city and obj.city.timezone) else "Asia/Kolkata"
        tz = ZoneInfo(tz_name)
        now = timezone.now().astimezone(tz)
        
        check_time = obj.end_time if obj.end_time else obj.event_time
        event_dt = timezone.datetime.combine(obj.event_date, check_time).replace(tzinfo=tz)
        if event_dt >= now:
            return "upcoming"
        return "completed"

    def get_organizer_name(self, obj) -> str:
        if obj.mosque:
            return obj.mosque.mosque_name
        if obj.city:
            return f"{obj.city.name} City Administration"
        return "City Administration"

    def get_published_by(self, obj) -> dict | None:
        # Mosque-scoped content must not receive City Admin attribution
        if obj.mosque_id is not None:
            return None

        user = obj.created_by
        city_admin = None
        if user and hasattr(user, "city_admin") and user.city_admin.is_active:
            city_admin = user.city_admin
        elif obj.city:
            from apps.accounts.models import CityAdmin
            city_admin = CityAdmin.objects.filter(city=obj.city, is_active=True).select_related("user").first()

        if not city_admin and not (user and hasattr(user, "city_admin")):
            return None

        ca_user = city_admin.user if city_admin else user
        full_name = f"{ca_user.first_name} {ca_user.last_name}".strip()
        if not full_name:
            full_name = ca_user.username

        city_name = obj.city.name if obj.city else (city_admin.city.name if city_admin and city_admin.city else "")

        return {
            "name": full_name,
            "role": "City Administrator",
            "city": city_name,
        }


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
        try:
            engine = MosqueAvailabilityEngine(obj)
            return engine.get_availability()
        except (ValueError, TypeError, AttributeError, ZoneInfoNotFoundError) as exc:
            import logging
            logging.getLogger(__name__).warning("Error calculating operating status for mosque %s: %s", getattr(obj, "id", None), exc)
            return {
                "is_open": False,
                "status_label": "Schedule Not Verified",
                "current_window": None,
                "closes_at": None,
                "opens_at": None,
                "next_prayer_name": None,
                "next_prayer_time": None,
            }

    def get_prayer_timing(self, obj) -> dict | None:
        try:
            from apps.prayers.services import CongregationTimingResolver
            from apps.prayers.serializers import ResolvedPrayerTimingSerializer
            from apps.prayers.models import PrayerTiming
            from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
            from django.utils import timezone
            
            try:
                timing = obj.prayer_timing
            except (PrayerTiming.DoesNotExist, AttributeError):
                return None

            if not timing:
                return None

            date_val = self.context.get("date")
            if not date_val:
                city = obj.city_relation
                tz_name = city.timezone if (city and city.timezone) else "Asia/Kolkata"
                try:
                    tz = ZoneInfo(tz_name)
                except (ZoneInfoNotFoundError, KeyError, ValueError, TypeError):
                    tz = ZoneInfo("Asia/Kolkata")
                date_val = timezone.now().astimezone(tz).date()

            resolved = CongregationTimingResolver.resolve_prayer_timing(timing, date_val)
            if not resolved:
                return None

            payload = {
                "fajr_time": resolved.fajr_time,
                "dhuhr_time": resolved.dhuhr_time,
                "asr_time": resolved.asr_time,
                "maghrib_time": resolved.maghrib_time,
                "isha_time": resolved.isha_time,
                "jumuah_time": resolved.jumuah_time,
                "effective_from": resolved.effective_from,
                "maghrib_congregation_mode": resolved.maghrib_congregation_mode,
                "updated_at": timing.updated_at if getattr(timing, "updated_at", None) else None,
            }
            return ResolvedPrayerTimingSerializer(payload).data
        except (ValueError, TypeError, AttributeError, ZoneInfoNotFoundError) as exc:
            import logging
            logging.getLogger(__name__).warning("Error serializing prayer timing for mosque %s: %s", getattr(obj, "id", None), exc)
            return None


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
            "latitude",
            "longitude",
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

        # Auto-extract coordinates if missing
        url_target = attrs.get("google_maps_url") or attrs.get("google_maps_link")
        if url_target and (attrs.get("latitude") is None or attrs.get("longitude") is None):
            from apps.mosques.services import extract_coordinates_from_url
            lat, lon = extract_coordinates_from_url(url_target)
            if lat is not None and lon is not None:
                attrs["latitude"] = lat
                attrs["longitude"] = lon

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

        # Authoritative City selection validation (RC-BUG-007)
        from apps.locations.models import City
        city_input = attrs.get("city", "").strip()
        city_obj = None
        if city_input:
            import string
            normalized = " ".join(city_input.split()).strip(string.punctuation).lower()
            city_obj = City.objects.filter(name__iexact=normalized).first()
            if not city_obj:
                city_obj = City.objects.filter(name__icontains=normalized).first()

        if not city_obj:
            raise serializers.ValidationError(
                {"city": "Please select a valid registered City from the platform city directory."}
            )

        attrs["city_relation"] = city_obj
        attrs["city"] = city_obj.name
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

        city_relation_id = attrs.get("city_relation_id")
        if city_relation_id is not None:
            try:
                city_obj = City.objects.get(id=city_relation_id)
                attrs["city_relation"] = city_obj
                attrs["city"] = city_obj.name
            except City.DoesNotExist:
                raise serializers.ValidationError({"city": "City with this ID does not exist."})
        elif "city" in attrs:
            city_name = attrs.get("city", "").strip()
            city_obj = None
            if city_name:
                import string
                normalized = " ".join(city_name.split()).strip(string.punctuation).lower()
                city_obj = City.objects.filter(name__iexact=normalized).first()
                if not city_obj:
                    city_obj = City.objects.filter(name__icontains=normalized).first()
            if not city_obj:
                raise serializers.ValidationError({"city": "Please select a valid registered City from the platform city directory."})
            attrs["city_relation"] = city_obj
            attrs["city"] = city_obj.name
                
        return attrs


class MosqueOperatingScheduleSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.ReadOnlyField(source="updated_by.username")

    class Meta:
        model = MosqueOperatingSchedule
        fields = (
            "id",
            "mosque",
            "schedule_mode",
            "open_24_hours",
            "general_open_time",
            "general_close_time",
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

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = data.copy()
            time_fields = (
                "general_open_time",
                "general_close_time",
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
            )
            for field in time_fields:
                if field in data and (data[field] == "" or data[field] is None or (isinstance(data[field], str) and not data[field].strip())):
                    data[field] = None
        return super().to_internal_value(data)

    def validate(self, attrs):
        schedule_mode = attrs.get(
            "schedule_mode",
            getattr(self.instance, "schedule_mode", "SALAH_BASED") if self.instance else "SALAH_BASED"
        )
        open_24 = attrs.get("open_24_hours", None)

        if schedule_mode == "24_HOURS" or open_24 is True:
            attrs["schedule_mode"] = "24_HOURS"
            attrs["open_24_hours"] = True
        elif schedule_mode == "GENERAL":
            attrs["open_24_hours"] = False
            gen_open = attrs.get(
                "general_open_time",
                getattr(self.instance, "general_open_time", None) if self.instance else None
            )
            gen_close = attrs.get(
                "general_close_time",
                getattr(self.instance, "general_close_time", None) if self.instance else None
            )
            if not gen_open or not gen_close:
                raise serializers.ValidationError(
                    "Opening and closing times are required for General Open-Close operating mode."
                )
        elif schedule_mode == "SALAH_BASED":
            attrs["open_24_hours"] = False

        return attrs




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

