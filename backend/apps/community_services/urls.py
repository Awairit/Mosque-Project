from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.community_services.views import JanazahNoticeViewSet, DashboardJanazahNoticeViewSet

router = DefaultRouter()
router.register(r"dashboard/janazah", DashboardJanazahNoticeViewSet, basename="dashboard-janazah")
router.register(r"janazah", JanazahNoticeViewSet, basename="public-janazah")

urlpatterns = [
    path("", include(router.urls)),
]
