from django.urls import path
from apps.analytics.views import (
    TrackVisitAPIView,
    SuperAdminAnalyticsOverviewAPIView,
    CityAdminAnalyticsAPIView,
)

urlpatterns = [
    path("track/", TrackVisitAPIView.as_view(), name="analytics-track"),
    path("overview/", SuperAdminAnalyticsOverviewAPIView.as_view(), name="analytics-overview"),
    path("city-admin/", CityAdminAnalyticsAPIView.as_view(), name="analytics-city-admin"),
]
