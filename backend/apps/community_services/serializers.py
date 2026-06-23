from rest_framework import serializers
from apps.community_services.models import JanazahNotice
from apps.mosques.models import Mosque


class JanazahNoticeSerializer(serializers.ModelSerializer):
    timezone = serializers.SerializerMethodField()
    mosque_name = serializers.CharField(source="mosque.mosque_name", read_only=True)
    mosque = serializers.PrimaryKeyRelatedField(
        queryset=Mosque.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = JanazahNotice
        fields = [
            "id",
            "mosque",
            "mosque_name",
            "deceased_name",
            "gender",
            "age",
            "date_of_death",
            "salah_date",
            "salah_time",
            "salah_details",
            "burial_date",
            "burial_time",
            "cemetery_name",
            "cemetery_address",
            "cemetery_gps_url",
            "family_contact_name",
            "family_contact_phone",
            "publish_contact_info",
            "status",
            "version",
            "timezone",
            "created_at",
            "updated_at",
            "published_at",
            "cancelled_at",
            "archived_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "published_at",
            "cancelled_at",
            "archived_at",
        ]

    def get_timezone(self, obj):
        if obj.mosque and obj.mosque.city_relation:
            return obj.mosque.city_relation.timezone
        return "UTC"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get("request")
        # Check if requested through dashboard or public view
        is_dashboard = request and "dashboard" in request.path if request else False

        if not is_dashboard and not instance.publish_contact_info:
            ret["family_contact_name"] = None
            ret["family_contact_phone"] = None
        return ret

    def validate(self, attrs):
        # We need to perform model validation checks on updates/creates
        # Date of death is mandatory in our database model, but during updates it could be partial
        # Get values from attrs or instance
        instance = self.instance
        request = self.context.get("request")

        mosque = attrs.get("mosque")
        if not mosque:
            if instance:
                mosque = instance.mosque
            elif request and request.user and hasattr(request.user, "mosque_admin"):
                mosque = request.user.mosque_admin.mosque
            attrs["mosque"] = mosque

        date_of_death = attrs.get("date_of_death", instance.date_of_death if instance else None)
        salah_date = attrs.get("salah_date", instance.salah_date if instance else None)
        burial_date = attrs.get("burial_date", instance.burial_date if instance else None)

        # Enforce date validations
        # Get localized date today
        from zoneinfo import ZoneInfo
        from django.utils import timezone
        
        if mosque and mosque.city_relation and mosque.city_relation.timezone:
            tz = ZoneInfo(mosque.city_relation.timezone)
            today = timezone.localtime(timezone.now()).astimezone(tz).date()
        else:
            today = timezone.localdate()

        if date_of_death and date_of_death > today:
            raise serializers.ValidationError({"date_of_death": "Date of death cannot be in the future."})

        if salah_date and date_of_death and salah_date < date_of_death:
            raise serializers.ValidationError({"salah_date": "Salah date cannot be before the date of death."})

        if burial_date and salah_date and burial_date < salah_date:
            raise serializers.ValidationError({"burial_date": "Burial date cannot be before the Salah date."})

        return attrs

    def update(self, instance, validated_data):
        # Optimistic Locking increment version
        validated_data["version"] = instance.version + 1
        return super().update(instance, validated_data)
