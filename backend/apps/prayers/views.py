"""Views for managing prayer timings."""

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsMosqueAdmin
from apps.prayers.models import PrayerTiming
from apps.prayers.serializers import PrayerTimingSerializer


class DashboardPrayerTimingAPIView(APIView):
    """API endpoints for authenticated mosque admins to manage their timings."""

    permission_classes = [IsMosqueAdmin]

    def get(self, request):
        mosque = request.user.mosque_admin.mosque
        timing, _ = PrayerTiming.objects.get_or_create(
            mosque=mosque,
            defaults={
                "fajr_time": "05:00:00",
                "dhuhr_time": "13:30:00",
                "asr_time": "17:00:00",
                "maghrib_time": "19:00:00",
                "isha_time": "20:30:00",
                "jumuah_time": "13:30:00",
                "effective_from": timezone.now().date(),
                "updated_by": request.user,
            },
        )
        serializer = PrayerTimingSerializer(timing)
        return Response(serializer.data)

    def put(self, request):
        mosque = request.user.mosque_admin.mosque
        timing, _ = PrayerTiming.objects.get_or_create(
            mosque=mosque,
            defaults={
                "fajr_time": "05:00:00",
                "dhuhr_time": "13:30:00",
                "asr_time": "17:00:00",
                "maghrib_time": "19:00:00",
                "isha_time": "20:30:00",
                "jumuah_time": "13:30:00",
                "effective_from": timezone.now().date(),
            },
        )
        serializer = PrayerTimingSerializer(
            timing, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data)
