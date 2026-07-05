"""Views for managing prayer timings."""

from datetime import time
from zoneinfo import ZoneInfo
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsMosqueAdmin
from apps.prayers.models import PrayerTiming
from apps.prayers.serializers import PrayerTimingSerializer
from apps.prayers.services import CongregationTimingResolver, ensure_time


class DashboardPrayerTimingAPIView(APIView):
    """API endpoints for authenticated mosque admins to manage their timings."""

    permission_classes = [IsMosqueAdmin]

    def get(self, request):
        mosque = request.user.mosque_admin.mosque
        timing, _ = PrayerTiming.objects.get_or_create(
            mosque=mosque,
            defaults={
                "fajr_time": time(5, 0),
                "dhuhr_time": time(13, 30),
                "asr_time": time(17, 0),
                "maghrib_time": time(19, 0),
                "isha_time": time(20, 30),
                "jumuah_time": time(13, 30),
                "effective_from": timezone.now().date(),
                "maghrib_congregation_mode": PrayerTiming.CongregationMode.MANUAL,
                "updated_by": request.user,
            },
        )
        
        # Resolve today's date in mosque city timezone
        city = mosque.city_relation
        tz_name = city.timezone if (city and city.timezone) else "Asia/Kolkata"
        today_date = timezone.now().astimezone(ZoneInfo(tz_name)).date()
        
        serializer = PrayerTimingSerializer(timing)
        data = serializer.data
        
        resolved = CongregationTimingResolver.resolve_prayer_timing(timing, today_date)
        if resolved:
            data["resolved_maghrib_time"] = resolved.maghrib_time.strftime("%H:%M:%S")
        else:
            data["resolved_maghrib_time"] = ensure_time(timing.maghrib_time).strftime("%H:%M:%S")
            
        return Response(data)

    def put(self, request):
        mosque = request.user.mosque_admin.mosque
        timing, _ = PrayerTiming.objects.get_or_create(
            mosque=mosque,
            defaults={
                "fajr_time": time(5, 0),
                "dhuhr_time": time(13, 30),
                "asr_time": time(17, 0),
                "maghrib_time": time(19, 0),
                "isha_time": time(20, 30),
                "jumuah_time": time(13, 30),
                "effective_from": timezone.now().date(),
                "maghrib_congregation_mode": PrayerTiming.CongregationMode.MANUAL,
            },
        )
        
        data = request.data.copy()
        
        # If user updates maghrib_time but does not send maghrib_congregation_mode,
        # we default to MANUAL override to preserve manual entries.
        if "maghrib_time" in data and "maghrib_congregation_mode" not in data:
            data["maghrib_congregation_mode"] = PrayerTiming.CongregationMode.MANUAL
            
        serializer = PrayerTimingSerializer(
            timing, data=data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        
        # Fetch today's date in mosque city timezone
        city = mosque.city_relation
        tz_name = city.timezone if (city and city.timezone) else "Asia/Kolkata"
        today_date = timezone.now().astimezone(ZoneInfo(tz_name)).date()
        
        res_data = serializer.data
        resolved = CongregationTimingResolver.resolve_prayer_timing(timing, today_date)
        if resolved:
            res_data["resolved_maghrib_time"] = resolved.maghrib_time.strftime("%H:%M:%S")
        else:
            res_data["resolved_maghrib_time"] = ensure_time(timing.maghrib_time).strftime("%H:%M:%S")
            
        return Response(res_data)
