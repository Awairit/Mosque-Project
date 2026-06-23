"""Serializers for location-related APIs."""

from rest_framework import serializers

from apps.locations.models import City, CityPrayerTiming, CityDailyPrayerTiming


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ("id", "name", "timezone", "latitude", "longitude")


class CityPrayerTimingSerializer(serializers.ModelSerializer):
    city_name = serializers.ReadOnlyField(source="city.name")

    class Meta:
        model = CityPrayerTiming
        fields = (
            "id",
            "city",
            "city_name",
            "calendar_date",
            "fajr_time",
            "dhuhr_time",
            "asr_time",
            "maghrib_time",
            "isha_time",
        )


class CityDailyPrayerTimingSerializer(serializers.ModelSerializer):
    city_name = serializers.ReadOnlyField(source="city.name")
    calendar_date = serializers.SerializerMethodField()

    class Meta:
        model = CityDailyPrayerTiming
        fields = (
            "id",
            "city",
            "city_name",
            "calendar_date",
            "fajr_time",
            "sunrise_time",
            "dhuhr_time",
            "asr_time",
            "maghrib_time",
            "isha_time",
        )

    def get_calendar_date(self, obj) -> str:
        return obj.date.strftime("%Y-%m-%d")

