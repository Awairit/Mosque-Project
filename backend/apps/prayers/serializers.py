"""Serializers for prayer timings."""

from rest_framework import serializers

from apps.prayers.models import PrayerTiming


class ResolvedPrayerTimingSerializer(serializers.Serializer):
    fajr_time = serializers.TimeField(format="%H:%M:%S")
    dhuhr_time = serializers.TimeField(format="%H:%M:%S")
    asr_time = serializers.TimeField(format="%H:%M:%S")
    maghrib_time = serializers.TimeField(format="%H:%M:%S")
    isha_time = serializers.TimeField(format="%H:%M:%S")
    jumuah_time = serializers.TimeField(format="%H:%M:%S")
    effective_from = serializers.DateField(format="%Y-%m-%d")
    maghrib_congregation_mode = serializers.CharField()


class PrayerTimingSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.ReadOnlyField(source="updated_by.username")

    class Meta:
        model = PrayerTiming
        fields = (
            "id",
            "mosque",
            "fajr_time",
            "dhuhr_time",
            "asr_time",
            "maghrib_time",
            "isha_time",
            "jumuah_time",
            "effective_from",
            "maghrib_congregation_mode",
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
