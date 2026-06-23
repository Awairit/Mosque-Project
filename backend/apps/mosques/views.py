"""API views for mosque-related workflows."""

import math
from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Prefetch
from django.utils import timezone

from apps.accounts.permissions import IsMosqueAdmin
from apps.common.utils.geo import calculate_haversine
from apps.mosques.models import (
    Mosque,
    MosqueOperatingSchedule,
    MosquePhoto,
    MosqueAnnouncement,
    MosqueEvent,
    CommunitySchedule,
)
from apps.mosques.serializers import (
    MosqueOperatingScheduleSerializer,
    MosqueProfileSerializer,
    MosqueRegistrationRequestSerializer,
    MosqueSerializer,
    MosquePhotoSerializer,
    MosqueAnnouncementSerializer,
    MosqueEventSerializer,
    CommunityScheduleSerializer,
)


from apps.community_services.models import JanazahNotice


def get_optimized_mosque_queryset():
    today = timezone.localdate()
    return Mosque.objects.filter(
        mosque_status=Mosque.MosqueStatus.ACTIVE
    ).select_related(
        "operating_schedule",
        "prayer_timing",
        "prayer_timing__updated_by",
        "city_relation",
    ).prefetch_related(
        Prefetch(
            "photos",
            queryset=MosquePhoto.objects.filter(is_active=True).order_by("display_order"),
        ),
        Prefetch(
            "announcements",
            queryset=MosqueAnnouncement.objects.filter(
                is_active=True,
                status="published",
                start_date__lte=today,
                end_date__gte=today,
            ).order_by("-created_at"),
        ),
        Prefetch(
            "events",
            queryset=MosqueEvent.objects.filter(
                is_active=True,
                status="published",
                event_date__gte=today,
            ).order_by("event_date", "event_time"),
        ),
        Prefetch(
            "schedules",
            queryset=CommunitySchedule.objects.filter(
                event_date__gte=today,
            ).order_by("event_date", "start_time"),
        ),
        Prefetch(
            "janazah_notices",
            queryset=JanazahNotice.objects.filter(
                status="published",
            ).order_by("-salah_date", "-salah_time"),
        ),
    )


class MosqueListAPIView(ListAPIView):
    serializer_class = MosqueSerializer
    permission_classes = [AllowAny]
    throttle_scope = "burst"

    def get_queryset(self):
        queryset = get_optimized_mosque_queryset()

        # Viewport Bounding Box Filter
        bbox = self.request.query_params.get("in_bbox")
        if bbox:
            try:
                sw_lat, sw_lon, ne_lat, ne_lon = map(float, bbox.split(","))
                queryset = queryset.filter(
                    latitude__range=(sw_lat, ne_lat),
                    longitude__range=(sw_lon, ne_lon)
                )
            except ValueError:
                pass

        # Facility and Accommodation Filters
        if self.request.query_params.get("women_prayer_available") == "true":
            queryset = queryset.filter(women_prayer_available=True)
        if self.request.query_params.get("wudu_facility_available") == "true":
            queryset = queryset.filter(wudu_facility_available=True)
        if self.request.query_params.get("parking_available") == "true":
            queryset = queryset.filter(parking_available=True)
        if self.request.query_params.get("wheelchair_accessible") == "true":
            queryset = queryset.filter(wheelchair_accessible=True)
        if self.request.query_params.get("jumuah_available") == "true":
            queryset = queryset.filter(prayer_timing__isnull=False, prayer_timing__jumuah_time__isnull=False)

        return queryset.order_by("mosque_name")

    def list(self, request, *args, **kwargs):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        in_bbox = request.query_params.get("in_bbox")
        open_now = request.query_params.get("open_now") == "true"

        queryset = self.get_queryset()

        user_lat = None
        user_lon = None
        if lat is not None and lon is not None:
            try:
                user_lat = float(lat)
                user_lon = float(lon)
            except ValueError:
                pass

        if user_lat is not None and user_lon is not None and not in_bbox:
            # Proximity pre-filtering for Top 5 list fallback (100 km radius)
            radius_km = 100.0
            lat_delta = radius_km / 111.1
            min_lat = user_lat - lat_delta
            max_lat = user_lat + lat_delta

            cos_lat = math.cos(math.radians(user_lat))
            lon_delta = radius_km / (111.1 * cos_lat) if cos_lat > 0.01 else radius_km / 111.1
            min_lon = user_lon - lon_delta
            max_lon = user_lon + lon_delta

            candidates = queryset.filter(
                latitude__range=(min_lat, max_lat),
                longitude__range=(min_lon, max_lon),
            )
            if candidates.count() < 5:
                candidates = queryset
        else:
            candidates = queryset

        # Compute dynamic filters and distances
        filtered_candidates = []
        for m in candidates:
            if open_now:
                from apps.mosques.services import MosqueAvailabilityEngine
                engine = MosqueAvailabilityEngine(m)
                avail = engine.get_availability()
                if not avail.get("is_open"):
                    continue

            if user_lat is not None and user_lon is not None and m.latitude is not None and m.longitude is not None:
                m.distance_val = calculate_haversine(user_lat, user_lon, m.latitude, m.longitude)
            else:
                m.distance_val = None

            filtered_candidates.append(m)

        # Distance sorting and Top 5 slicing
        if user_lat is not None and user_lon is not None:
            filtered_candidates.sort(key=lambda x: x.distance_val if x.distance_val is not None else float('inf'))
            if not in_bbox:
                filtered_candidates = filtered_candidates[:5]

        serializer = self.get_serializer(
            filtered_candidates,
            many=True,
            context={"request": request, "lat": user_lat, "lon": user_lon}
        )
        return Response({
            "count": len(serializer.data),
            "results": serializer.data
        })


class MosqueDetailAPIView(RetrieveAPIView):
    """Fetches full configuration details for a specific active mosque."""

    serializer_class = MosqueSerializer
    permission_classes = [AllowAny]
    throttle_scope = "burst"

    def get_queryset(self):
        return get_optimized_mosque_queryset()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lat = self.request.query_params.get("lat")
        lon = self.request.query_params.get("lon")
        if lat is not None and lon is not None:
            try:
                context["lat"] = float(lat)
                context["lon"] = float(lon)
            except ValueError:
                pass
        return context


class MosqueRegistrationRequestCreateAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "sensitive"

    def post(self, request):
        serializer = MosqueRegistrationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        registration_request = serializer.save()

        return Response(
            {
                "message": (
                    "Your mosque registration request has been submitted successfully. "
                    "Our team will contact you after verification."
                ),
                "request_id": registration_request.id,
                "status": registration_request.status,
            },
            status=status.HTTP_201_CREATED,
        )


class DashboardMosqueProfileAPIView(APIView):
    """Endpoints for authenticated mosque admins to manage their mosque's profile & facilities."""

    permission_classes = [IsMosqueAdmin]

    def get(self, request):
        mosque = request.user.mosque_admin.mosque
        serializer = MosqueProfileSerializer(mosque)
        return Response(serializer.data)

    def put(self, request):
        mosque = request.user.mosque_admin.mosque
        serializer = MosqueProfileSerializer(
            mosque, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DashboardOperatingScheduleAPIView(APIView):
    """Endpoints for authenticated mosque admins to manage their operating schedule."""

    permission_classes = [IsMosqueAdmin]

    def get(self, request):
        mosque = request.user.mosque_admin.mosque
        # Idempotently retrieve or create an empty schedule record as per user refinements
        schedule, _ = MosqueOperatingSchedule.objects.get_or_create(
            mosque=mosque,
            defaults={
                "open_24_hours": False,
                "fajr_open": None,
                "fajr_close": None,
                "dhuhr_open": None,
                "dhuhr_close": None,
                "asr_open": None,
                "asr_close": None,
                "maghrib_open": None,
                "maghrib_close": None,
                "isha_open": None,
                "isha_close": None,
                "updated_by": request.user,
            },
        )
        serializer = MosqueOperatingScheduleSerializer(schedule)
        return Response(serializer.data)

    def put(self, request):
        mosque = request.user.mosque_admin.mosque
        schedule, _ = MosqueOperatingSchedule.objects.get_or_create(
            mosque=mosque,
            defaults={
                "open_24_hours": False,
            },
        )
        serializer = MosqueOperatingScheduleSerializer(
            schedule, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data)


class DashboardMosquePhotoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsMosqueAdmin]
    serializer_class = MosquePhotoSerializer
    pagination_class = None

    def get_queryset(self):
        return MosquePhoto.objects.filter(mosque=self.request.user.mosque_admin.mosque)

    def perform_create(self, serializer):
        serializer.save(
            mosque=self.request.user.mosque_admin.mosque,
            uploaded_by=self.request.user
        )


class DashboardMosqueAnnouncementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsMosqueAdmin]
    serializer_class = MosqueAnnouncementSerializer
    pagination_class = None

    def get_queryset(self):
        return MosqueAnnouncement.objects.filter(mosque=self.request.user.mosque_admin.mosque)

    def perform_create(self, serializer):
        serializer.save(
            mosque=self.request.user.mosque_admin.mosque,
            created_by=self.request.user
        )


class DashboardMosqueEventViewSet(viewsets.ModelViewSet):
    permission_classes = [IsMosqueAdmin]
    serializer_class = MosqueEventSerializer
    pagination_class = None

    def get_queryset(self):
        return MosqueEvent.objects.filter(mosque=self.request.user.mosque_admin.mosque)

    def perform_create(self, serializer):
        serializer.save(
            mosque=self.request.user.mosque_admin.mosque,
            created_by=self.request.user
        )


class DashboardCommunityScheduleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsMosqueAdmin]
    serializer_class = CommunityScheduleSerializer
    pagination_class = None

    def get_queryset(self):
        return CommunitySchedule.objects.filter(mosque=self.request.user.mosque_admin.mosque)

    def perform_create(self, serializer):
        serializer.save(
            mosque=self.request.user.mosque_admin.mosque,
        )

