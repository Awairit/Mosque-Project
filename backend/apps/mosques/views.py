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

        # City Filters
        city_param = self.request.query_params.get("city")
        if city_param and city_param.strip():
            c_name = city_param.strip()
            queryset = queryset.filter(Q(city__iexact=c_name) | Q(city_relation__name__iexact=c_name))

        city_id_param = self.request.query_params.get("city_id")
        if city_id_param:
            try:
                queryset = queryset.filter(city_relation_id=int(city_id_param))
            except ValueError:
                pass

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
        import logging
        logger = logging.getLogger(__name__)
        stage = "1_start"

        try:
            stage = "2_get_queryset"
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
                    longitude__range=(min_lon, max_lon)
                )
                if candidates.count() < 5:
                    candidates = queryset
            else:
                candidates = queryset

            stage = "3_evaluate_candidates_query"
            candidate_list = list(candidates)

            stage = "4_haversine_distance_calculation"
            for m in candidate_list:
                m_lat = float(m.latitude) if m.latitude is not None else None
                m_lon = float(m.longitude) if m.longitude is not None else None

                if user_lat is not None and user_lon is not None and m_lat is not None and m_lon is not None:
                    m.distance_val = calculate_haversine(user_lat, user_lon, m_lat, m_lon)
                else:
                    m.distance_val = None

            if user_lat is not None and user_lon is not None:
                candidate_list.sort(key=lambda x: x.distance_val if x.distance_val is not None else float('inf'))

            stage = "5_open_now_filtering_and_slicing"
            target_limit = None if in_bbox else 5
            filtered_candidates = []

            if open_now:
                from apps.mosques.services import MosqueAvailabilityEngine
                for m in candidate_list:
                    engine = MosqueAvailabilityEngine(m)
                    avail = engine.get_availability()
                    if avail.get("is_open"):
                        filtered_candidates.append(m)
                        if target_limit and len(filtered_candidates) >= target_limit:
                            break
            else:
                if target_limit:
                    filtered_candidates = candidate_list[:target_limit]
                else:
                    filtered_candidates = candidate_list

            stage = "6_serializer_instantiation"
            serializer = self.get_serializer(
                filtered_candidates,
                many=True,
                context={"request": request, "lat": user_lat, "lon": user_lon}
            )

            stage = "7_serializer_data_evaluation"
            data = serializer.data

            stage = "8_response_construction"
            mosque_ids = [m.id for m in filtered_candidates]
            logger.info(
                "[DIAGNOSTIC_SUCCESS] Path='%s' | QueryParams=%s | CandidatesCount=%d | FilteredCount=%d | MosqueIDs=%s",
                request.path,
                dict(request.query_params),
                len(candidate_list),
                len(filtered_candidates),
                mosque_ids,
            )
            return Response({
                "count": len(data),
                "results": data
            })
        except Exception as exc:
            logger.error(
                "[DIAGNOSTIC_FAILURE] Stage='%s' | Path='%s' | QueryParams=%s | Exception=%s: %s",
                stage,
                request.path,
                dict(request.query_params),
                type(exc).__name__,
                exc,
                exc_info=True,
            )
            raise exc


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

    def patch(self, request):
        return self.put(request)


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
        return MosqueAnnouncement.objects.filter(city=city_admin.city, mosque__isnull=True)

    def perform_create(self, serializer):
        city_admin = self.request.user.city_admin
        mosque = serializer.validated_data.get("mosque")
        if mosque and mosque.city_relation != city_admin.city:
            raise ValidationError("You can only assign announcements to mosques in your city.")
        serializer.save(
            city=city_admin.city,
            mosque=None,
            created_by=self.request.user
        )

    def perform_update(self, serializer):
        city_admin = self.request.user.city_admin
        mosque = serializer.validated_data.get("mosque")
        if mosque and mosque.city_relation != city_admin.city:
            raise ValidationError("You can only assign announcements to mosques in your city.")
        serializer.save(
            city=city_admin.city,
            mosque=None
        )


class CityAdminEventViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCityAdmin]
    serializer_class = MosqueEventSerializer

    def get_queryset(self):
        city_admin = self.request.user.city_admin
        return MosqueEvent.objects.filter(city=city_admin.city, mosque__isnull=True)

    def perform_create(self, serializer):
        city_admin = self.request.user.city_admin
        mosque = serializer.validated_data.get("mosque")
        if mosque and mosque.city_relation != city_admin.city:
            raise ValidationError("You can only assign events to mosques in your city.")
        serializer.save(
            city=city_admin.city,
            mosque=None,
            created_by=self.request.user
        )

    def perform_update(self, serializer):
        city_admin = self.request.user.city_admin
        mosque = serializer.validated_data.get("mosque")
        if mosque and mosque.city_relation != city_admin.city:
            raise ValidationError("You can only assign events to mosques in your city.")
        serializer.save(
            city=city_admin.city,
            mosque=None
        )


class CityAdminMosqueListAPIView(ListAPIView):
    """
    Lists all mosques located in the assigned City Admin's city.
    Requires IsCityAdmin permission.
    """
    permission_classes = [IsCityAdmin]
    serializer_class = MosqueListSerializer

    def get_queryset(self):
        city_admin = self.request.user.city_admin
        city = city_admin.city
        from django.db.models import Q
        return Mosque.objects.filter(
            Q(city_relation=city) | Q(city__iexact=city.name)
        ).select_related("city_relation").order_by("mosque_name")


class CityAdminMosqueStatusAPIView(APIView):
    """
    Allows a City Admin to update status (active, inactive, archived) for a mosque in their assigned city.
    Enforces backend city scoping.
    """
    permission_classes = [IsCityAdmin]

    def patch(self, request, pk):
        city_admin = request.user.city_admin
        from django.db.models import Q
        try:
            mosque = Mosque.objects.get(
                Q(pk=pk) & (Q(city_relation=city_admin.city) | Q(city__iexact=city_admin.city.name))
            )
        except Mosque.DoesNotExist:
            return Response({"detail": "Mosque not found or does not belong to your assigned city."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("mosque_status")
        if new_status not in [Mosque.MosqueStatus.ACTIVE, Mosque.MosqueStatus.INACTIVE, Mosque.MosqueStatus.ARCHIVED]:
            return Response({"detail": "Invalid mosque status. Must be 'active', 'inactive', or 'archived'."}, status=status.HTTP_400_BAD_REQUEST)

        old_status = mosque.mosque_status
        mosque.mosque_status = new_status
        mosque.save(update_fields=["mosque_status", "updated_at"])

        from apps.accounts.models import MosqueAdmin, IdentityAuditLog
        if new_status in [Mosque.MosqueStatus.INACTIVE, Mosque.MosqueStatus.ARCHIVED]:
            admins = MosqueAdmin.objects.filter(mosque=mosque)
            for admin in admins:
                admin.is_active = False
                admin.user.is_active = False
                admin.user.save(update_fields=["is_active"])
                admin.save(update_fields=["is_active", "updated_at"])
        elif new_status == Mosque.MosqueStatus.ACTIVE:
            admins = MosqueAdmin.objects.filter(mosque=mosque)
            for admin in admins:
                admin.is_active = True
                admin.user.is_active = True
                admin.user.save(update_fields=["is_active"])
                admin.save(update_fields=["is_active", "updated_at"])

        IdentityAuditLog.objects.create(
            user=request.user,
            action=IdentityAuditLog.Action.MOSQUE_STATUS_CHANGED,
            metadata={
                "mosque_id": mosque.id,
                "mosque_name": mosque.mosque_name,
                "old_status": old_status,
                "new_status": new_status,
                "changed_by": request.user.username,
                "role": "city_admin",
            }
        )

        return Response({
            "detail": f"Mosque status updated to {new_status}.",
            "id": mosque.id,
            "mosque_status": mosque.mosque_status
        }, status=status.HTTP_200_OK)



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
        from django.db.models import Q
        queryset = MosqueAnnouncement.objects.select_related(
            "created_by", "city", "created_by__city_admin"
        ).filter(
            is_active=True,
            status="published",
            start_date__lte=today,
            end_date__gte=today
        )
        mosque_id = self.request.query_params.get("mosque_id")
        city_id = self.request.query_params.get("city_id")
        city_name = self.request.query_params.get("city")

        if mosque_id:
            queryset = queryset.filter(mosque_id=mosque_id)
        elif city_id:
            queryset = queryset.filter(city_id=city_id, mosque__isnull=True)
        elif city_name:
            queryset = queryset.filter(city__name__iexact=city_name, mosque__isnull=True)

        return queryset.order_by("-priority", "-created_at")



class PublicEventListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = MosqueEventSerializer
    pagination_class = None

    def get_queryset(self):
        from django.db.models import Q
        from zoneinfo import ZoneInfo
        now = timezone.now().astimezone(ZoneInfo("Asia/Kolkata"))
        today = now.date()
        current_time = now.time()

        queryset = MosqueEvent.objects.select_related(
            "created_by", "city", "created_by__city_admin"
        ).filter(
            is_active=True,
            status="published",
        ).filter(
            Q(event_date__gt=today) |
            Q(event_date=today, end_time__gte=current_time) |
            Q(event_date=today, end_time__isnull=True, event_time__gte=current_time)
        )
        mosque_id = self.request.query_params.get("mosque_id")
        city_id = self.request.query_params.get("city_id")

        if mosque_id:
            queryset = queryset.filter(mosque_id=mosque_id)
        elif city_id:
            queryset = queryset.filter(city_id=city_id, mosque__isnull=True)

        return queryset.order_by("event_date", "event_time")


class CityAdminDashboardStatsAPIView(APIView):
    permission_classes = [IsCityAdmin]

    def get(self, request):
        from django.db.models import Count, Q
        city_admin = request.user.city_admin
        city = city_admin.city
        today = timezone.localdate()
        now = timezone.now()

        # Announcements stats (Single-pass database aggregation)
        announcements_qs = MosqueAnnouncement.objects.filter(city=city)
        ann_stats = announcements_qs.aggregate(
            total=Count("id"),
            published=Count("id", filter=Q(status="published", start_date__lte=today, end_date__gte=today)),
            draft=Count("id", filter=Q(status="draft")),
            scheduled=Count("id", filter=Q(status="published", start_date__gt=today)),
            expired=Count("id", filter=Q(end_date__lt=today)),
            emergency=Count("id", filter=Q(announcement_type="emergency", status="published", start_date__lte=today, end_date__gte=today)),
        )

        # Events stats (Single-pass database aggregation)
        events_qs = MosqueEvent.objects.filter(city=city)
        evt_stats = events_qs.aggregate(
            total=Count("id"),
            upcoming=Count("id", filter=Q(event_date__gt=today)),
            ongoing=Count("id", filter=Q(event_date=today)),
            completed=Count("id", filter=Q(event_date__lt=today)),
        )

        # Recent activities
        recent_announcements = announcements_qs.only("id", "title", "created_at").order_by("-created_at")[:5]
        recent_events = events_qs.only("id", "title", "created_at", "event_date").order_by("-created_at")[:5]

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
                "total": ann_stats["total"] or 0,
                "published": ann_stats["published"] or 0,
                "draft": ann_stats["draft"] or 0,
                "scheduled": ann_stats["scheduled"] or 0,
                "expired": ann_stats["expired"] or 0,
            },
            "events": {
                "total": evt_stats["total"] or 0,
                "upcoming": evt_stats["upcoming"] or 0,
                "ongoing": evt_stats["ongoing"] or 0,
                "completed": evt_stats["completed"] or 0,
            },
            "emergency_alerts": ann_stats["emergency"] or 0,
            "recent_activity": recent_activity
        }, status=status.HTTP_200_OK)



