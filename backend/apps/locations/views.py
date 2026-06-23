"""API views for location-related workflows."""

from datetime import date
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.utils.geo import calculate_haversine
from apps.locations.models import City, CityPrayerTiming, CityDailyPrayerTiming
from apps.locations.serializers import CitySerializer, CityPrayerTimingSerializer, CityDailyPrayerTimingSerializer


class CityListAPIView(ListAPIView):
    """Lists all available cities sorted alphabetically."""

    serializer_class = CitySerializer
    permission_classes = [AllowAny]
    queryset = City.objects.all().order_by("name")


class CityPrayerTimingAPIView(APIView):
    """API view to fetch prayer timings for a city.

    Supports:
    - GPS auto-detection: if 'lat' and 'lon' query parameters are passed, finds the nearest city.
    - Manual selection: if 'city' is passed (either as an ID or name), resolves that city.
    - Default fallback: returns the first alphabetical city.
    """

    permission_classes = [AllowAny]
    throttle_scope = "burst"

    def get(self, request):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        city_param = request.query_params.get("city")

        resolved_city = None

        # 1. GPS Auto-detection
        if lat is not None and lon is not None:
            try:
                user_lat = float(lat)
                user_lon = float(lon)
                cities = list(City.objects.all())
                if cities:
                    # Calculate distance to all cities and find the nearest one
                    cities_with_dist = []
                    for c in cities:
                        dist = calculate_haversine(user_lat, user_lon, c.latitude, c.longitude)
                        cities_with_dist.append((c, dist))
                    cities_with_dist.sort(key=lambda x: x[1])
                    resolved_city = cities_with_dist[0][0]
            except ValueError:
                pass

        # 2. Manual Selection
        if resolved_city is None and city_param:
            # Try to resolve by ID
            if city_param.isdigit():
                resolved_city = City.objects.filter(id=int(city_param)).first()
            # Try to resolve by Name
            if resolved_city is None:
                resolved_city = City.objects.filter(name__iexact=city_param).first()

        # 3. Default Fallback (first city alphabetically)
        if resolved_city is None:
            resolved_city = City.objects.all().order_by("name").first()

        if resolved_city is None:
            return Response(
                {"detail": "No cities are registered in the system."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from zoneinfo import ZoneInfo
        tz_name = resolved_city.timezone or "Asia/Kolkata"
        today = timezone.now().astimezone(ZoneInfo(tz_name)).date()

        # Prioritize daily calendar imports, then fall back to baseline defaults
        daily_timing = CityDailyPrayerTiming.objects.filter(city=resolved_city, date=today).first()
        if daily_timing:
            serializer = CityDailyPrayerTimingSerializer(daily_timing)
            data = serializer.data
            data["city_details"] = CitySerializer(resolved_city).data
            return Response(data)

        # Find specific calendar date first, otherwise fall back to static baseline timing (calendar_date=None)
        timing = (
            CityPrayerTiming.objects.filter(city=resolved_city, calendar_date=today).first()
            or CityPrayerTiming.objects.filter(city=resolved_city, calendar_date=None).first()
        )

        if not timing:
            return Response(
                {"detail": f"No prayer timings configured for city '{resolved_city.name}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CityPrayerTimingSerializer(timing)
        data = serializer.data
        data["city_details"] = CitySerializer(resolved_city).data
        return Response(data)

