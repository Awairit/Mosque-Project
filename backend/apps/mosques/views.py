"""API views for mosque-related workflows."""

import math
from rest_framework import status, viewsets
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Prefetch, Q
from django.utils import timezone
from apps.common.utils.strings import normalize_phone_number

from rest_framework.exceptions import ValidationError
from apps.accounts.permissions import IsMosqueAdmin, IsCityAdmin
from apps.common.utils.geo import calculate_haversine
from apps.common.services.notification import notification_service
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
    MosqueListSerializer,
    MosqueDetailSerializer,
    MosquePhotoSerializer,
    MosqueAnnouncementSerializer,
    MosqueEventSerializer,
    CommunityScheduleSerializer,
)


from apps.community_services.models import JanazahNotice


def get_optimized_mosque_queryset(prefetch_details: bool = True):
    today = timezone.localdate()
    from apps.locations.models import CityDailyPrayerTiming
    qs = Mosque.objects.filter(
        mosque_status=Mosque.MosqueStatus.ACTIVE
    ).select_related(
        "operating_schedule",
        "prayer_timing",
        "prayer_timing__updated_by",
        "city_relation",
    ).prefetch_related(
        Prefetch(
            "city_relation__daily_prayer_timings",
            queryset=CityDailyPrayerTiming.objects.filter(date=today),
            to_attr="today_daily_timing"
        )
    )

    if prefetch_details:
        qs = qs.prefetch_related(
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
    return qs


class MosqueListAPIView(ListAPIView):
    serializer_class = MosqueListSerializer
    permission_classes = [AllowAny]
    throttle_scope = "burst"

    def get_queryset(self):
        queryset = get_optimized_mosque_queryset(prefetch_details=False)

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

    serializer_class = MosqueDetailSerializer
    permission_classes = [AllowAny]
    throttle_scope = "burst"

    def get_queryset(self):
        return get_optimized_mosque_queryset(prefetch_details=True)

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


class RegistrationOTPRequestAPIView(APIView):
    """Step 1 of registration — send OTP to WhatsApp number."""
    permission_classes = [AllowAny]
    throttle_scope = "sensitive"

    def post(self, request):
        mobile_number = request.data.get("mobile_number", "").strip()
        if not mobile_number:
            return Response({"mobile_number": ["WhatsApp number is required."]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            normalized = normalize_phone_number(mobile_number)
        except ValueError as exc:
            return Response({"mobile_number": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        # Guard: mobile already registered as an active admin (checking normalized and local)
        from django.contrib.auth.models import User as DjangoUser
        local_digits = normalized.replace("+91", "")
        existing = DjangoUser.objects.filter(
            Q(username=normalized) | Q(username=local_digits)
        ).first()
        if existing and hasattr(existing, "mosque_admin"):
            return Response({"mobile_number": ["This number is already registered."]}, status=status.HTTP_400_BAD_REQUEST)

        from apps.common.services.otp import OTPService
        from apps.common.services.otp_providers import OTPErrorCode

        result = OTPService.generate_and_send_otp(mobile_number=normalized, purpose="registration")

        if not result.success:
            if result.code == OTPErrorCode.RATE_LIMITED:
                return Response({"mobile_number": [result.message]}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            elif result.code in (OTPErrorCode.PROVIDER_UNAVAILABLE, OTPErrorCode.CONFIGURATION_ERROR):
                return Response({"mobile_number": [result.message]}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                return Response({"mobile_number": [result.message]}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "OTP sent to your WhatsApp number."}, status=status.HTTP_200_OK)


class RegistrationOTPVerifyAPIView(APIView):
    """Step 2 of registration — verify the OTP."""
    permission_classes = [AllowAny]
    throttle_scope = "sensitive"

    def post(self, request):
        mobile_number = request.data.get("mobile_number", "").strip()
        otp = request.data.get("otp", "").strip()

        if not mobile_number or not otp:
            return Response({"non_field_errors": ["Mobile number and OTP are required."]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            normalized = normalize_phone_number(mobile_number)
        except ValueError as exc:
            return Response({"non_field_errors": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        from apps.common.services.otp import OTPService
        from apps.common.services.otp_providers import OTPErrorCode
        
        result = OTPService.verify_otp(mobile_number=normalized, purpose="registration", otp=otp)

        if not result.success:
            if result.code == OTPErrorCode.RATE_LIMITED:
                return Response({"non_field_errors": [result.message]}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            elif result.code in (OTPErrorCode.PROVIDER_UNAVAILABLE, OTPErrorCode.CONFIGURATION_ERROR):
                return Response({"non_field_errors": [result.message]}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                return Response({"non_field_errors": [result.message]}, status=status.HTTP_400_BAD_REQUEST)

        # Issue a short-lived verification token signed with the E.164 number
        from django.core.signing import TimestampSigner
        signer = TimestampSigner()
        verification_token = signer.sign(normalized)

        return Response({
            "detail": "WhatsApp number verified successfully.",
            "verification_token": verification_token,
        }, status=status.HTTP_200_OK)


class MosqueRegistrationRequestCreateAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "sensitive"

    def post(self, request):
        # Require a valid verification_token from the OTP step
        verification_token = request.data.get("verification_token", "").strip()
        if not verification_token:
            return Response({"non_field_errors": ["WhatsApp verification is required before submitting."]}, status=status.HTTP_400_BAD_REQUEST)

        from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
        signer = TimestampSigner()
        try:
            # Token is valid for 30 minutes
            verified_mobile = signer.unsign(verification_token, max_age=1800)
            verified_normalized = normalize_phone_number(verified_mobile)
        except (BadSignature, SignatureExpired, ValueError):
            return Response({"non_field_errors": ["Verification token expired. Please re-verify your WhatsApp number."]}, status=status.HTTP_400_BAD_REQUEST)

        # Make sure submitted mobile matches the verified mobile
        submitted_mobile = request.data.get("mobile_number", "").strip()
        try:
            submitted_normalized = normalize_phone_number(submitted_mobile)
        except ValueError as exc:
            return Response({"mobile_number": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        if submitted_normalized != verified_normalized:
            return Response({"mobile_number": ["Mobile number does not match the verified number."]}, status=status.HTTP_400_BAD_REQUEST)

        serializer = MosqueRegistrationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        from django.utils import timezone as tz
        now = tz.now()
        registration_request = serializer.save(
            whatsapp_verified=True,
            whatsapp_verified_at=now,
            mobile_verified=True,
            verification_method="whatsapp_otp",
            verification_timestamp=now,
            status="pending",
        )

        from apps.accounts.models import IdentityAuditLog
        IdentityAuditLog.objects.create(
            user=None,
            action=IdentityAuditLog.Action.REGISTRATION_SUBMITTED,
            metadata={
                "registration_request_id": registration_request.id,
                "mosque_name": registration_request.mosque_name,
                "mobile_number": registration_request.mobile_number,
            }
        )

        return Response(
            {
                "message": (
                    "Your WhatsApp number has been verified and registration has been submitted. "
                    "Our Super Admin will contact you on your verified WhatsApp number to complete verification. "
                    "After approval, you will receive your temporary login credentials."
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
        mosque = self.request.user.mosque_admin.mosque
        serializer.save(
            mosque=mosque,
            city=mosque.city_relation,
            created_by=self.request.user
        )


class DashboardMosqueEventViewSet(viewsets.ModelViewSet):
    permission_classes = [IsMosqueAdmin]
    serializer_class = MosqueEventSerializer
    pagination_class = None

    def get_queryset(self):
        return MosqueEvent.objects.filter(mosque=self.request.user.mosque_admin.mosque)

    def perform_create(self, serializer):
        mosque = self.request.user.mosque_admin.mosque
        serializer.save(
            mosque=mosque,
            city=mosque.city_relation,
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


class CityAdminAnnouncementViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCityAdmin]
    serializer_class = MosqueAnnouncementSerializer

    def get_queryset(self):
        city_admin = self.request.user.city_admin
        return MosqueAnnouncement.objects.filter(city=city_admin.city)

    def perform_create(self, serializer):
        city_admin = self.request.user.city_admin
        mosque = serializer.validated_data.get("mosque")
        if mosque and mosque.city_relation != city_admin.city:
            raise ValidationError("You can only assign announcements to mosques in your city.")
        serializer.save(
            city=city_admin.city,
            created_by=self.request.user
        )

    def perform_update(self, serializer):
        city_admin = self.request.user.city_admin
        mosque = serializer.validated_data.get("mosque")
        if mosque and mosque.city_relation != city_admin.city:
            raise ValidationError("You can only assign announcements to mosques in your city.")
        serializer.save()


class CityAdminEventViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCityAdmin]
    serializer_class = MosqueEventSerializer

    def get_queryset(self):
        city_admin = self.request.user.city_admin
        return MosqueEvent.objects.filter(city=city_admin.city)

    def perform_create(self, serializer):
        city_admin = self.request.user.city_admin
        mosque = serializer.validated_data.get("mosque")
        if mosque and mosque.city_relation != city_admin.city:
            raise ValidationError("You can only assign events to mosques in your city.")
        serializer.save(
            city=city_admin.city,
            created_by=self.request.user
        )

    def perform_update(self, serializer):
        city_admin = self.request.user.city_admin
        mosque = serializer.validated_data.get("mosque")
        if mosque and mosque.city_relation != city_admin.city:
            raise ValidationError("You can only assign events to mosques in your city.")
        serializer.save()


class CityAdminNotificationSendAPIView(APIView):
    permission_classes = [IsCityAdmin]

    def post(self, request, *args, **kwargs):
        city_admin = request.user.city_admin
        channel = request.data.get("channel")  # e.g., 'whatsapp', 'sms', 'email', 'push', 'in_app'
        recipient = request.data.get("recipient")
        message = request.data.get("message")
        title = request.data.get("title", "City Notification")
        subject = request.data.get("subject", "City Notice")
        metadata = request.data.get("metadata", {})

        if not channel or not recipient or not message:
            raise ValidationError("Fields 'channel', 'recipient', and 'message' are required.")

        # Recipient Authorization Checks to prevent cross-city spam or arbitrary relays
        from rest_framework.exceptions import PermissionDenied
        from django.db.models import Q
        from apps.common.utils.strings import normalize_phone_number
        from apps.accounts.models import MosqueAdmin, CityAdmin

        city = city_admin.city
        is_authorized = False

        if channel in ["sms", "whatsapp"]:
            try:
                normalized = normalize_phone_number(recipient)
            except ValueError:
                normalized = recipient
            local_digits = normalized.replace("+91", "")
            
            if MosqueAdmin.objects.filter(
                Q(mobile_number=normalized) | Q(mobile_number=local_digits),
                mosque__city_relation=city
            ).exists():
                is_authorized = True
            elif CityAdmin.objects.filter(
                Q(mobile_number=normalized) | Q(mobile_number=local_digits),
                city=city
            ).exists():
                is_authorized = True

        elif channel == "email":
            if MosqueAdmin.objects.filter(
                user__email=recipient,
                mosque__city_relation=city
            ).exists():
                is_authorized = True
            elif CityAdmin.objects.filter(
                user__email=recipient,
                city=city
            ).exists():
                is_authorized = True

        elif channel == "in_app":
            try:
                user_id = int(recipient)
                if MosqueAdmin.objects.filter(
                    user_id=user_id,
                    mosque__city_relation=city
                ).exists():
                    is_authorized = True
                elif CityAdmin.objects.filter(
                    user_id=user_id,
                    city=city
                ).exists():
                    is_authorized = True
            except ValueError:
                raise ValidationError("Recipient for in_app must be a numeric user ID.")

        elif channel == "push":
            # For push, check if recipient user is within the city admin's city boundaries
            # Check user_id in metadata
            user_id = metadata.get("user_id")
            if user_id:
                try:
                    user_id = int(user_id)
                    if MosqueAdmin.objects.filter(user_id=user_id, mosque__city_relation=city).exists() or \
                       CityAdmin.objects.filter(user_id=user_id, city=city).exists():
                        is_authorized = True
                except ValueError:
                    pass

            if not is_authorized:
                # Try as user ID
                try:
                    u_id = int(recipient)
                    if MosqueAdmin.objects.filter(user_id=u_id, mosque__city_relation=city).exists() or \
                       CityAdmin.objects.filter(user_id=u_id, city=city).exists():
                        is_authorized = True
                except ValueError:
                    pass
            # Try as email
            if not is_authorized:
                if MosqueAdmin.objects.filter(user__email=recipient, mosque__city_relation=city).exists() or \
                   CityAdmin.objects.filter(user__email=recipient, city=city).exists():
                    is_authorized = True
            # Try as phone
            if not is_authorized:
                try:
                    normalized = normalize_phone_number(recipient)
                except ValueError:
                    normalized = recipient
                local_digits = normalized.replace("+91", "")
                if MosqueAdmin.objects.filter(Q(mobile_number=normalized) | Q(mobile_number=local_digits), mosque__city_relation=city).exists() or \
                   CityAdmin.objects.filter(Q(mobile_number=normalized) | Q(mobile_number=local_digits), city=city).exists():
                    is_authorized = True

        if not is_authorized:
            raise PermissionDenied("You are not authorized to send notifications to this recipient.")

        success = False
        if channel == "whatsapp":
            success = notification_service.send_whatsapp(recipient, message, metadata)
        elif channel == "sms":
            success = notification_service.send_sms(recipient, message, metadata)
        elif channel == "email":
            success = notification_service.send_email(recipient, subject, message, metadata)
        elif channel == "push":
            success = notification_service.send_push(recipient, title, message, metadata)
        elif channel == "in_app":
            try:
                user_id = int(recipient)
                success = notification_service.send_in_app(user_id, title, message, metadata)
            except ValueError:
                raise ValidationError("Recipient for in_app must be a numeric user ID.")
        else:
            raise ValidationError(f"Invalid channel '{channel}'. Supported: whatsapp, sms, email, push, in_app.")

        return Response({
            "success": success,
            "message": "Notification dispatched." if success else "Failed to dispatch notification."
        }, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)



class PublicAnnouncementListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = MosqueAnnouncementSerializer
    pagination_class = None

    def get_queryset(self):
        today = timezone.localdate()
        queryset = MosqueAnnouncement.objects.filter(
            is_active=True,
            status="published",
            start_date__lte=today,
            end_date__gte=today
        )
        city_id = self.request.query_params.get("city_id")
        if city_id:
            queryset = queryset.filter(city_id=city_id)
        mosque_id = self.request.query_params.get("mosque_id")
        if mosque_id:
            queryset = queryset.filter(mosque_id=mosque_id)
        return queryset.order_by("-priority", "-created_at")


class PublicEventListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = MosqueEventSerializer
    pagination_class = None

    def get_queryset(self):
        today = timezone.localdate()
        queryset = MosqueEvent.objects.filter(
            is_active=True,
            status="published",
            event_date__gte=today
        )
        city_id = self.request.query_params.get("city_id")
        if city_id:
            queryset = queryset.filter(city_id=city_id)
        mosque_id = self.request.query_params.get("mosque_id")
        if mosque_id:
            queryset = queryset.filter(mosque_id=mosque_id)
        return queryset.order_by("event_date", "event_time")


class CityAdminDashboardStatsAPIView(APIView):
    permission_classes = [IsCityAdmin]

    def get(self, request):
        city_admin = request.user.city_admin
        city = city_admin.city
        today = timezone.localdate()
        now = timezone.now()

        # Announcements stats
        announcements_qs = MosqueAnnouncement.objects.filter(city=city)
        total_announcements = announcements_qs.count()
        published_announcements = announcements_qs.filter(status="published", start_date__lte=today, end_date__gte=today).count()
        draft_announcements = announcements_qs.filter(status="draft").count()
        scheduled_announcements = announcements_qs.filter(status="published", start_date__gt=today).count()
        expired_announcements = announcements_qs.filter(end_date__lt=today).count()

        # Events stats
        events_qs = MosqueEvent.objects.filter(city=city)
        total_events = events_qs.count()
        upcoming_events = events_qs.filter(event_date__gt=today).count()
        ongoing_events = events_qs.filter(event_date=today).count()
        completed_events = events_qs.filter(event_date__lt=today).count()

        # Emergency alerts count
        emergency_alerts = announcements_qs.filter(
            announcement_type="emergency",
            status="published",
            start_date__lte=today,
            end_date__gte=today
        ).count()

        # Recent activities
        recent_announcements = announcements_qs.order_by("-created_at")[:5]
        recent_events = events_qs.order_by("-created_at")[:5]

        recent_activity = []
        for ann in recent_announcements:
            recent_activity.append({
                "id": f"ann-{ann.id}",
                "type": "announcement",
                "title": ann.title,
                "created_at": ann.created_at,
                "action": "Announcement Created",
                "description": f"Announcement '{ann.title}' was created"
            })
        for evt in recent_events:
            recent_activity.append({
                "id": f"evt-{evt.id}",
                "type": "event",
                "title": evt.title,
                "created_at": evt.created_at,
                "action": "Event Created",
                "description": f"Event '{evt.title}' was scheduled for {evt.event_date}"
            })

        recent_activity.sort(key=lambda x: x["created_at"], reverse=True)
        recent_activity = recent_activity[:5]

        for act in recent_activity:
            diff = now - act["created_at"]
            if diff.days == 0:
                if diff.seconds < 60:
                    time_str = "Just now"
                elif diff.seconds < 3600:
                    time_str = f"{diff.seconds // 60}m ago"
                else:
                    time_str = f"{diff.seconds // 3600}h ago"
            elif diff.days == 1:
                time_str = "Yesterday"
            else:
                time_str = act["created_at"].strftime("%b %d")
            act["time"] = time_str
            del act["created_at"]

        return Response({
            "announcements": {
                "total": total_announcements,
                "published": published_announcements,
                "draft": draft_announcements,
                "scheduled": scheduled_announcements,
                "expired": expired_announcements
            },
            "events": {
                "total": total_events,
                "upcoming": upcoming_events,
                "ongoing": ongoing_events,
                "completed": completed_events
            },
            "emergency_alerts": emergency_alerts,
            "recent_activity": recent_activity
        }, status=status.HTTP_200_OK)



