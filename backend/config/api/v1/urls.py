"""Version 1 API routes.

Each domain app owns its own URLs. Empty app URL files are included now so the
project stays modular as features are added.
"""

from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import LoginAPIView
from apps.mosques.views import (
    DashboardMosqueProfileAPIView,
    DashboardOperatingScheduleAPIView,
    MosqueRegistrationRequestCreateAPIView,
    DashboardMosquePhotoViewSet,
    DashboardMosqueAnnouncementViewSet,
    DashboardMosqueEventViewSet,
    DashboardCommunityScheduleViewSet,
)
from apps.prayers.views import DashboardPrayerTimingAPIView


def health_check(_request):
    return JsonResponse({"status": "ok", "api_version": "v1"})


router = DefaultRouter()
router.register(r"dashboard/photos", DashboardMosquePhotoViewSet, basename="dashboard-photos")
router.register(r"dashboard/announcements", DashboardMosqueAnnouncementViewSet, basename="dashboard-announcements")
router.register(r"dashboard/events", DashboardMosqueEventViewSet, basename="dashboard-events")
router.register(r"dashboard/schedules", DashboardCommunityScheduleViewSet, basename="dashboard-schedules")



urlpatterns = [
    path("health/", health_check, name="api-v1-health"),
    path(
        "auth/login/",
        LoginAPIView.as_view(),
        name="auth-login",
    ),
    path(
        "dashboard/mosque-profile/",
        DashboardMosqueProfileAPIView.as_view(),
        name="dashboard-mosque-profile",
    ),
    path(
        "dashboard/operating-schedule/",
        DashboardOperatingScheduleAPIView.as_view(),
        name="dashboard-operating-schedule",
    ),
    path(
        "dashboard/prayer-timings/",
        DashboardPrayerTimingAPIView.as_view(),
        name="dashboard-prayer-timings",
    ),
    path(
        "mosque-registration/",
        MosqueRegistrationRequestCreateAPIView.as_view(),
        name="public-mosque-registration",
    ),
    path("accounts/", include("apps.accounts.urls")),
    path("locations/", include("apps.locations.urls")),
    path("mosques/", include("apps.mosques.urls")),
    path("prayers/", include("apps.prayers.urls")),
    path("operations/", include("apps.operations.urls")),
    path("moderation/", include("apps.moderation.urls")),
    path("events/", include("apps.events.urls")),
    path("platform/", include("apps.platform_admin.urls")),
    path("", include("apps.community_services.urls")),
] + router.urls
