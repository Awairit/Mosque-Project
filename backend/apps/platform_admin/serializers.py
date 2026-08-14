"""Serializers for platform admin workflows."""

from rest_framework import serializers


class SuperAdminLoginSerializer(serializers.Serializer):
    """Serializer for super admin login request."""

    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


from apps.mosques.models import MosqueRegistrationRequest
from apps.locations.models import City

class CitySerializer(serializers.ModelSerializer):
    timetable_status = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = (
            "id", "name", "latitude", "longitude", "timezone", 
            "timetable_policy", "acknowledged_timetable_year", "timetable_status",
            "created_at", "updated_at"
        )
        read_only_fields = ("id", "timetable_status", "created_at", "updated_at")

    def to_internal_value(self, data):
        if isinstance(data, dict) and "timetable_policy" in data:
            val = data.get("timetable_policy")
            mapping = {
                "Annual Upload Required": "ANNUAL_UPLOAD",
                "Continue Previous Timetable Until Replaced": "CONTINUE_PREVIOUS",
                "Astronomical Calculation (Future)": "ASTRONOMICAL",
                "Official Authority Source (Future)": "AUTHORITY",
            }
            if val in mapping:
                data = data.copy()
                data["timetable_policy"] = mapping[val]
        return super().to_internal_value(data)


    def get_timetable_status(self, obj):
        from apps.locations.models import CityDailyPrayerTiming
        from django.utils import timezone
        
        latest_timing = CityDailyPrayerTiming.objects.filter(city=obj).order_by("-date").first()
        latest_year = latest_timing.date.year if latest_timing else None
        
        current_year = timezone.now().year
        
        needs_update = False
        if latest_year is None or latest_year < current_year:
            if obj.timetable_policy == "ANNUAL_UPLOAD":
                if obj.acknowledged_timetable_year != current_year:
                    needs_update = True
        
        return {
            "latest_uploaded_year": latest_year,
            "current_year": current_year,
            "needs_update": needs_update
        }


from apps.accounts.models import CityAdmin

class CityAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)
    city_id = serializers.IntegerField(source="city.id", read_only=True)
    mosque_id = serializers.SerializerMethodField()
    mosque_name = serializers.SerializerMethodField()

    def get_mosque_id(self, obj):
        if hasattr(obj.user, "mosque_admin") and obj.user.mosque_admin.is_active and obj.user.mosque_admin.mosque:
            return obj.user.mosque_admin.mosque.id
        return None

    def get_mosque_name(self, obj):
        if hasattr(obj.user, "mosque_admin") and obj.user.mosque_admin.is_active and obj.user.mosque_admin.mosque:
            return obj.user.mosque_admin.mosque.mosque_name
        return None

    class Meta:
        model = CityAdmin
        fields = (
            "id",
            "user_id",
            "username",
            "email",
            "first_name",
            "last_name",
            "mobile_number",
            "city_id",
            "city_name",
            "mosque_id",
            "mosque_name",
            "is_active",
            "must_change_password",
            "temporary_password_expires_at",
            "password_changed_at",
            "last_password_reset_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "user_id",
            "must_change_password",
            "temporary_password_expires_at",
            "password_changed_at",
            "last_password_reset_at",
            "created_at",
            "updated_at",
        )


class SuperAdminMosqueRegistrationRequestSerializer(serializers.ModelSerializer):
    approved_by_username = serializers.CharField(source="approved_by.username", read_only=True)
    rejected_by_username = serializers.CharField(source="rejected_by.username", read_only=True)
    under_verification_by_username = serializers.CharField(source="under_verification_by.username", read_only=True)
    duplicate_info = serializers.SerializerMethodField()

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
            "city_raw",
            "address",
            "google_maps_link",
            "google_maps_url",
            "women_prayer_available",
            "notes",
            "status",
            "mobile_verified",
            "whatsapp_verified",
            "whatsapp_verified_at",
            "verification_method",
            "verification_timestamp",
            "under_verification_at",
            "under_verification_by",
            "under_verification_by_username",
            "super_admin_notes",
            "created_at",
            "updated_at",
            "approved_by",
            "approved_by_username",
            "approved_at",
            "rejected_by",
            "rejected_by_username",
            "rejected_at",
            "rejection_reason",
            "duplicate_info",
        )

    def get_duplicate_info(self, obj):
        from django.contrib.auth.models import User
        
        mobile_number = obj.mobile_number.strip() if obj.mobile_number else ""
        email = obj.email.strip() if obj.email else ""
        
        # Check mobile number
        if mobile_number:
            existing_user = User.objects.filter(username=mobile_number).first()
            if existing_user and hasattr(existing_user, 'mosque_admin'):
                mosque_admin = existing_user.mosque_admin
                return {
                    "duplicate": True,
                    "reason": "mobile_number_exists",
                    "message": "This phone number is already assigned to another Mosque Administrator.",
                    "existing_admin": {
                        "name": existing_user.first_name or "Mosque Admin",
                        "mosque": mosque_admin.mosque.mosque_name if mosque_admin.mosque else "Unknown",
                        "city": mosque_admin.mosque.city if mosque_admin.mosque else "Unknown",
                        "status": "Active" if mosque_admin.is_active else "Inactive"
                    }
                }
                
        # Check email
        if email:
            existing_user = User.objects.filter(email=email).exclude(email="").first()
            if existing_user and hasattr(existing_user, 'mosque_admin'):
                mosque_admin = existing_user.mosque_admin
                return {
                    "duplicate": True,
                    "reason": "email_exists",
                    "message": "This email address is already being used by another Mosque Administrator.",
                    "existing_admin": {
                        "name": existing_user.first_name or "Mosque Admin",
                        "mosque": mosque_admin.mosque.mosque_name if mosque_admin.mosque else "Unknown",
                        "city": mosque_admin.mosque.city if mosque_admin.mosque else "Unknown",
                        "status": "Active" if mosque_admin.is_active else "Inactive"
                    }
                }
                
        return None


from apps.accounts.models import AccountRecoveryRequest

class AccountRecoveryRequestSerializer(serializers.ModelSerializer):
    reviewed_by_username = serializers.CharField(source="reviewed_by.username", read_only=True)
    reopened_by_username = serializers.CharField(source="reopened_by.username", read_only=True)

    class Meta:
        model = AccountRecoveryRequest
        fields = (
            "id",
            "mosque",
            "mosque_name",
            "applicant_name",
            "previous_registered_contact",
            "contact_email",
            "contact_whatsapp",
            "notes",
            "status",
            "reviewed_by",
            "reviewed_by_username",
            "reviewed_at",
            "review_notes",
            "reopened_by",
            "reopened_by_username",
            "reopened_at",
            "target_user",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "reviewed_by", "reviewed_at", "reopened_by", "reopened_at")

