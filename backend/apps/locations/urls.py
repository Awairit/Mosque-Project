"""Location API routes."""

from django.urls import path

from apps.locations.views import CityListAPIView, CityPrayerTimingAPIView

urlpatterns = [
    path("cities/", CityListAPIView.as_view(), name="city-list"),
    path("city-timings/", CityPrayerTimingAPIView.as_view(), name="city-timings"),
]
