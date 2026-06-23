"""Django admin registrations for prayer workflows."""

from django.contrib import admin

from apps.prayers.models import PrayerTiming


@admin.register(PrayerTiming)
class PrayerTimingAdmin(admin.ModelAdmin):
    list_display = (
        "mosque",
        "effective_from",
        "updated_by",
        "updated_at",
    )
    list_filter = ("effective_from", "updated_at")
    search_fields = ("mosque__mosque_name", "updated_by__username")
    readonly_fields = ("created_at", "updated_at")
