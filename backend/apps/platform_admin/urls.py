"""Platform admin URL routes mapping."""

from django.urls import path

from apps.platform_admin.views import (
    SuperAdminDashboardStatsAPIView,
    SuperAdminLoginAPIView,
    SuperAdminRegistrationRequestListAPIView,
    SuperAdminRegistrationRequestDetailAPIView,
    SuperAdminRegistrationRequestApproveAPIView,
    SuperAdminRegistrationRequestRejectAPIView,
    SuperAdminMarkUnderVerificationAPIView,
    SuperAdminVerificationNotesAPIView,
    SuperAdminResetMosqueAdminPasswordAPIView,
    SuperAdminCityListCreateAPIView,
    SuperAdminCityDetailAPIView,
    SuperAdminCityTimetableAPIView,
    SuperAdminCityTimetableAcknowledgeAPIView,
)

urlpatterns = [
    path("auth/login/", SuperAdminLoginAPIView.as_view(), name="platform-admin-login"),
    path("dashboard/stats/", SuperAdminDashboardStatsAPIView.as_view(), name="platform-admin-stats"),
    path("requests/", SuperAdminRegistrationRequestListAPIView.as_view(), name="platform-admin-requests-list"),
    path("requests/<int:pk>/", SuperAdminRegistrationRequestDetailAPIView.as_view(), name="platform-admin-requests-detail"),
    path("requests/<int:pk>/approve/", SuperAdminRegistrationRequestApproveAPIView.as_view(), name="platform-admin-requests-approve"),
    path("requests/<int:pk>/reject/", SuperAdminRegistrationRequestRejectAPIView.as_view(), name="platform-admin-requests-reject"),
    path("requests/<int:pk>/mark-under-verification/", SuperAdminMarkUnderVerificationAPIView.as_view(), name="platform-admin-requests-under-verification"),
    path("requests/<int:pk>/verification-notes/", SuperAdminVerificationNotesAPIView.as_view(), name="platform-admin-requests-verification-notes"),
    path("requests/<int:pk>/reset-password/", SuperAdminResetMosqueAdminPasswordAPIView.as_view(), name="platform-admin-request-reset-password"),
    path("cities/", SuperAdminCityListCreateAPIView.as_view(), name="platform-admin-cities-list"),
    path("cities/<int:pk>/", SuperAdminCityDetailAPIView.as_view(), name="platform-admin-cities-detail"),
    path("cities/<int:pk>/timetables/<str:action>/", SuperAdminCityTimetableAPIView.as_view(), name="platform-admin-cities-timetables"),
    path("cities/<int:pk>/timetables-acknowledge/", SuperAdminCityTimetableAcknowledgeAPIView.as_view(), name="platform-admin-cities-timetables-acknowledge"),
]
