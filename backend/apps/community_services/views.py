from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import APIException

from apps.accounts.permissions import IsMosqueAdmin, IsMosqueAdminOfObject
from apps.community_services.models import JanazahNotice
from apps.community_services.serializers import JanazahNoticeSerializer


class ConflictException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "This notice has been updated by another user. Please refresh and try again."
    default_code = "conflict"


class JanazahNoticeViewSet(viewsets.ReadOnlyModelViewSet):
    """Public read-only viewset for published Janazah notices."""
    serializer_class = JanazahNoticeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Only return published notices
        queryset = JanazahNotice.objects.filter(status=JanazahNotice.StatusChoices.PUBLISHED)

        # Optional filters
        mosque_id = self.request.query_params.get("mosque")
        if mosque_id:
            queryset = queryset.filter(mosque_id=mosque_id)

        city_id = self.request.query_params.get("city")
        if city_id:
            queryset = queryset.filter(mosque__city_relation_id=city_id)

        return queryset.select_related("mosque", "mosque__city_relation")


class DashboardJanazahNoticeViewSet(viewsets.ModelViewSet):
    """Admin dashboard viewset for mosque administrators to manage Janazah notices."""
    serializer_class = JanazahNoticeSerializer
    permission_classes = [IsAuthenticated, IsMosqueAdmin, IsMosqueAdminOfObject]
    pagination_class = None

    def get_queryset(self):
        if self.request.user.is_superuser:
            return JanazahNotice.objects.all()
        
        # Enforce multi-mosque isolation
        if hasattr(self.request.user, "mosque_admin"):
            return JanazahNotice.objects.filter(mosque=self.request.user.mosque_admin.mosque)
        
        return JanazahNotice.objects.none()

    def perform_create(self, serializer):
        # Force saving to the admin's linked mosque
        if not self.request.user.is_superuser and hasattr(self.request.user, "mosque_admin"):
            serializer.save(
                mosque=self.request.user.mosque_admin.mosque,
                created_by=self.request.user,
                updated_by=self.request.user
            )
        else:
            serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        # Validate optimistic locking version matches
        instance = self.get_object()
        client_version = self.request.data.get("version")
        if client_version is not None:
            try:
                client_version = int(client_version)
            except ValueError:
                pass
            if client_version != instance.version:
                raise ConflictException()

        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="send-correction")
    def send_correction(self, request, pk=None):
        notice = self.get_object()
        # Future extension hook for notification dispatch. Actual sending is forbidden in Phase 8A.
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Correction notification trigger simulated for JanazahNotice {notice.id}")
        return Response({
            "status": "correction_notification_queued",
            "notice_id": notice.id,
            "simulated": True
        })
