"""Version 1 API routes.

Each domain app owns its own URLs. Empty app URL files are included now so the
project stays modular as features are added.
"""

from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.accounts.views import (
    LoginAPIView, 
    ChangePasswordAPIView,
    ForgotPasswordRequestAPIView,
    ForgotPasswordVerifyAPIView,
    ForgotPasswordResetAPIView,
    AccountRecoveryRequestAPIView,
)
from apps.mosques.views import (
    DashboardMosqueProfileAPIView,
    DashboardOperatingScheduleAPIView,
    MosqueRegistrationRequestCreateAPIView,
    RegistrationOTPRequestAPIView,
    RegistrationOTPVerifyAPIView,
    DashboardMosquePhotoViewSet,
    DashboardMosqueAnnouncementViewSet,
    DashboardMosqueEventViewSet,
    DashboardCommunityScheduleViewSet,
    CityAdminAnnouncementViewSet,
    CityAdminEventViewSet,
    CityAdminNotificationSendAPIView,
    PublicAnnouncementListAPIView,
    PublicEventListAPIView,
    CityAdminDashboardStatsAPIView,
)
from apps.prayers.views import DashboardPrayerTimingAPIView


def health_check(_request):
    return JsonResponse({"status": "ok", "api_version": "v1"})


router = DefaultRouter()
router.register(r"dashboard/photos", DashboardMosquePhotoViewSet, basename="dashboard-photos")
router.register(r"dashboard/announcements", DashboardMosqueAnnouncementViewSet, basename="dashboard-announcements")
router.register(r"dashboard/events", DashboardMosqueEventViewSet, basename="dashboard-events")
router.register(r"dashboard/schedules", DashboardCommunityScheduleViewSet, basename="dashboard-schedules")
router.register(r"city-admin/announcements", CityAdminAnnouncementViewSet, basename="city-admin-announcements")
router.register(r"city-admin/events", CityAdminEventViewSet, basename="city-admin-events")



urlpatterns = [
    path("health/", health_check, name="api-v1-health"),
    path(
        "auth/login/",
        LoginAPIView.as_view(),
        name="auth-login",
    ),
    path(
        "auth/change-password/",
        ChangePasswordAPIView.as_view(),
        name="auth-change-password",
    ),
    path(
        "auth/forgot-password/request/",
        ForgotPasswordRequestAPIView.as_view(),
        name="auth-forgot-password-request",
    ),
    path(
        "auth/forgot-password/verify/",
        ForgotPasswordVerifyAPIView.as_view(),
        name="auth-forgot-password-verify",
    ),
    path(
        "auth/forgot-password/reset/",
        ForgotPasswordResetAPIView.as_view(),
        name="auth-forgot-password-reset",
    ),
    path(
        "auth/account-recovery/",
        AccountRecoveryRequestAPIView.as_view(),
        name="auth-account-recovery",
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
        "mosque-registration/otp/request/",
        RegistrationOTPRequestAPIView.as_view(),
        name="registration-otp-request",
    ),
    path(
        "mosque-registration/otp/verify/",
        RegistrationOTPVerifyAPIView.as_view(),
        name="registration-otp-verify",
    ),
    path(
        "mosque-registration/",
        MosqueRegistrationRequestCreateAPIView.as_view(),
        name="public-mosque-registration",
    ),
    path(
        "city-admin/notifications/send/",
        CityAdminNotificationSendAPIView.as_view(),
        name="city-admin-notifications-send",
    ),
    path(
        "city-admin/stats/",
        CityAdminDashboardStatsAPIView.as_view(),
        name="city-admin-dashboard-stats",
    ),
    path(
        "public/announcements/",
        PublicAnnouncementListAPIView.as_view(),
        name="public-announcements-list",
    ),
    path(
        "public/events/",
        PublicEventListAPIView.as_view(),
        name="public-events-list",
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
