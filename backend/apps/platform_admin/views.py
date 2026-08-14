"""Platform admin API views."""

import secrets
import string
import os
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import models, transaction, IntegrityError
from django.utils import timezone
from django.core.paginator import Paginator
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser, FormParser

from apps.locations.models import City
from apps.mosques.models import Mosque, MosqueRegistrationRequest
from apps.platform_admin.permissions import IsSuperUser
from apps.platform_admin.serializers import (
    SuperAdminLoginSerializer,
    SuperAdminMosqueRegistrationRequestSerializer,
    CitySerializer,
)
import traceback


class SuperAdminLoginAPIView(APIView):
    """API view for super admin login credentials verification and token generation."""

    permission_classes = [AllowAny]
    throttle_scope = "sensitive"

    def post(self, request):
        serializer = SuperAdminLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(username=username, password=password)
        if not user:
            return Response(
                {"non_field_errors": ["Invalid admin credentials."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_active or not user.is_superuser:
            return Response(
                {"non_field_errors": ["Access denied. This portal is restricted to system administrators."]},
                status=status.HTTP_403_FORBIDDEN,
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "username": user.username,
                "email": user.email,
                "role": "super_admin",
                "roles": ["super_admin"],
            },
            status=status.HTTP_200_OK,
        )


class SuperAdminDashboardStatsAPIView(APIView):
    """API view to retrieve statistical highlights for the platform control dashboard."""

    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request):
        pending_requests_count = MosqueRegistrationRequest.objects.filter(
            status=MosqueRegistrationRequest.Status.PENDING
        ).count()
        approved_mosques_count = Mosque.objects.count()
        cities_count = City.objects.count()

        # Placeholders for future implementations
        timetable_imports_count = 14  # Mock import feed logs count
        
        # Real database logs for recent activity feed
        from apps.platform_admin.models import MosqueApprovalLog
        logs = MosqueApprovalLog.objects.select_related("admin").all().order_by("-created_at")[:5]
        
        recent_activity = []
        for log in logs:
            diff = timezone.now() - log.created_at
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
                time_str = log.created_at.strftime("%b %d")

            action_str = "Mosque Approved" if log.action == MosqueApprovalLog.ActionTypes.APPROVE else "Mosque Rejected"
            details_str = f"Super admin @{log.admin.username} approved {log.mosque_name}" if log.action == MosqueApprovalLog.ActionTypes.APPROVE else f"Super admin @{log.admin.username} rejected {log.mosque_name}: {log.reason}"
            
            recent_activity.append({
                "id": log.id,
                "action": action_str,
                "details": details_str,
                "time": time_str
            })

        return Response(
            {
                "pending_mosque_requests": pending_requests_count,
                "approved_mosques": approved_mosques_count,
                "cities": cities_count,
                "prayer_timetable_imports": timetable_imports_count,
                "recent_activity": recent_activity,
                "system_status": "Healthy",
            },
            status=status.HTTP_200_OK,
        )


class SuperAdminRegistrationRequestListAPIView(APIView):
    """API view to list, search, filter, and paginate mosque registration requests."""

    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request):
        queryset = MosqueRegistrationRequest.objects.all().order_by("-created_at")

        # Filter by status
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Search query
        search_query = request.query_params.get("search")
        if search_query:
            queryset = queryset.filter(
                models.Q(mosque_name__icontains=search_query) |
                models.Q(admin_name__icontains=search_query) |
                models.Q(mobile_number__icontains=search_query) |
                models.Q(city__icontains=search_query)
            )

        # Pagination
        page_number = request.query_params.get("page", 1)
        page_size = request.query_params.get("page_size", 10)
        paginator = Paginator(queryset, page_size)

        try:
            page = paginator.page(page_number)
        except Exception:
            return Response(
                {"results": [], "count": 0, "num_pages": 0},
                status=status.HTTP_200_OK,
            )

        serializer = SuperAdminMosqueRegistrationRequestSerializer(page.object_list, many=True)
        return Response(
            {
                "results": serializer.data,
                "count": paginator.count,
                "num_pages": paginator.num_pages,
            },
            status=status.HTTP_200_OK,
        )


class SuperAdminRegistrationRequestDetailAPIView(APIView):
    """API view to retrieve detail information of a specific mosque registration request."""

    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request, pk):
        try:
            request_obj = MosqueRegistrationRequest.objects.get(pk=pk)
        except MosqueRegistrationRequest.DoesNotExist:
            return Response(
                {"detail": "Registration request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = SuperAdminMosqueRegistrationRequestSerializer(request_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SuperAdminResetMosqueAdminPasswordAPIView(APIView):
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, pk):
        from apps.accounts.models import PasswordAuditLog
        from rest_framework.authtoken.models import Token
        from django.shortcuts import get_object_or_404
        from datetime import timedelta
        import string
        import secrets

        request_obj = get_object_or_404(MosqueRegistrationRequest, pk=pk)
        if request_obj.status != MosqueRegistrationRequest.Status.APPROVED:
            return Response({"detail": "Request is not approved."}, status=status.HTTP_400_BAD_REQUEST)
            
        # The mosque is created with the same name and city, but we don't have a direct link on request.
        # Wait, the user who submitted the request is linked by mobile number!
        from django.contrib.auth.models import User
        user = get_object_or_404(User, username=request_obj.mobile_number)
        
        mosque_admin = getattr(user, 'mosque_admin', None)
        if not mosque_admin:
            return Response({"detail": "No admin found for this user."}, status=status.HTTP_400_BAD_REQUEST)

        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
        temp_password = ""
        while True:
            temp_password = "".join(secrets.choice(alphabet) for _ in range(14))
            if (any(c.islower() for c in temp_password)
                    and any(c.isupper() for c in temp_password)
                    and any(c.isdigit() for c in temp_password)
                    and any(c in "!@#$%^&*()_+-=" for c in temp_password)):
                break

        user.set_password(temp_password)
        user.save()

        mosque_admin.must_change_password = True
        mosque_admin.temporary_password_expires_at = timezone.now() + timedelta(days=7)
        mosque_admin.last_password_reset_at = timezone.now()
        mosque_admin.save()

        PasswordAuditLog.objects.create(
            user=user,
            performed_by=request.user,
            action=PasswordAuditLog.ActionTypes.RESET
        )

        Token.objects.filter(user=user).delete()

        return Response({
            "message": "Password reset successfully.",
            "temp_password": temp_password,
            "username": user.username
        }, status=status.HTTP_200_OK)


class SuperAdminRegistrationRequestApproveAPIView(APIView):
    """API view to approve a mosque registration request, creating the Mosque, User, and MosqueAdmin."""

    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, pk):
        approvable_statuses = [
            MosqueRegistrationRequest.Status.PENDING,
            MosqueRegistrationRequest.Status.UNDER_VERIFICATION,
            MosqueRegistrationRequest.Status.WHATSAPP_VERIFIED,
        ]

        from apps.mosques.services import approve_mosque_registration_request
        from django.contrib.auth.models import User

        try:
            with transaction.atomic():
                try:
                    request_obj = MosqueRegistrationRequest.objects.select_for_update().get(pk=pk)
                except MosqueRegistrationRequest.DoesNotExist:
                    return Response(
                        {"detail": "Registration request not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                if request_obj.status not in approvable_statuses:
                    return Response(
                        {"detail": "This registration request has already been processed by another administrator."},
                        status=status.HTTP_409_CONFLICT,
                    )

                username = request_obj.mobile_number.strip()
                existing_user_mobile = User.objects.filter(username=username).first()
                if existing_user_mobile and hasattr(existing_user_mobile, 'mosque_admin'):
                    return Response(
                        {"detail": "This phone number is already assigned to another Mosque Administrator."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                email = request_obj.email.strip() if request_obj.email else ""
                if email:
                    existing_user_email = User.objects.filter(email=email).exclude(email="").first()
                    if existing_user_email and hasattr(existing_user_email, 'mosque_admin'):
                        return Response(
                            {"detail": "This email address is already being used by another Mosque Administrator."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                result = approve_mosque_registration_request(request_obj, approved_by_user=request.user)
                response_password = result.get("temp_password")
                username = result["user"].username

        except Exception as e:
            return Response(
                {"detail": f"Failed to approve request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "detail": "Mosque registration request has been successfully approved.",
                "temp_password": response_password,
                "username": username,
            },
            status=status.HTTP_200_OK,
        )


class SuperAdminRegistrationRequestRejectAPIView(APIView):
    """API view to reject a mosque registration request with a mandatory rejection reason."""

    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, pk):
        rejectable_statuses = [
            MosqueRegistrationRequest.Status.PENDING,
            MosqueRegistrationRequest.Status.UNDER_VERIFICATION,
            MosqueRegistrationRequest.Status.WHATSAPP_VERIFIED,
        ]

        reason = request.data.get("reason", "").strip()
        if not reason:
            return Response(
                {"reason": ["Rejection reason is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.platform_admin.models import MosqueApprovalLog
        from apps.accounts.models import IdentityAuditLog

        try:
            with transaction.atomic():
                try:
                    request_obj = MosqueRegistrationRequest.objects.select_for_update().get(pk=pk)
                except MosqueRegistrationRequest.DoesNotExist:
                    return Response(
                        {"detail": "Registration request not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                if request_obj.status not in rejectable_statuses:
                    return Response(
                        {"detail": "This registration request has already been processed by another administrator."},
                        status=status.HTTP_409_CONFLICT,
                    )

                # Mark request as Rejected
                request_obj.status = MosqueRegistrationRequest.Status.REJECTED
                request_obj.rejected_by = request.user
                request_obj.rejected_at = timezone.now()
                request_obj.rejection_reason = reason
                request_obj.save()

                # Create audit record
                MosqueApprovalLog.objects.create(
                    action=MosqueApprovalLog.ActionTypes.REJECT,
                    mosque=None,
                    registration_request_id=request_obj.id,
                    mosque_name=request_obj.mosque_name,
                    admin=request.user,
                    reason=reason,
                )

                IdentityAuditLog.objects.create(
                    user=request.user,
                    action=IdentityAuditLog.Action.REGISTRATION_REJECTED,
                    metadata={
                        "registration_request_id": request_obj.id,
                        "mosque_name": request_obj.mosque_name,
                        "rejected_by": request.user.username,
                        "reason": reason,
                    }
                )
        except Exception as e:
            return Response(
                {"detail": f"Failed to reject request: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"detail": "Mosque registration request has been rejected."},
            status=status.HTTP_200_OK,
        )


class SuperAdminMarkUnderVerificationAPIView(APIView):
    """Mark a registration as Under Verification to indicate the Super Admin is actively reviewing it."""

    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, pk):
        try:
            request_obj = MosqueRegistrationRequest.objects.get(pk=pk)
        except MosqueRegistrationRequest.DoesNotExist:
            return Response({"detail": "Registration request not found."}, status=status.HTTP_404_NOT_FOUND)

        if request_obj.status not in [
            MosqueRegistrationRequest.Status.PENDING,
            MosqueRegistrationRequest.Status.WHATSAPP_VERIFIED,
        ]:
            return Response({"detail": "Request is not in a state that can be marked for verification."}, status=status.HTTP_400_BAD_REQUEST)

        request_obj.status = MosqueRegistrationRequest.Status.UNDER_VERIFICATION
        request_obj.under_verification_at = timezone.now()
        request_obj.under_verification_by = request.user
        request_obj.save(update_fields=["status", "under_verification_at", "under_verification_by", "updated_at"])

        from apps.accounts.models import IdentityAuditLog
        IdentityAuditLog.objects.create(
            user=request.user,
            action=IdentityAuditLog.Action.UNDER_VERIFICATION,
            metadata={
                "registration_request_id": request_obj.id,
                "mosque_name": request_obj.mosque_name,
                "marked_by": request.user.username,
            }
        )

        return Response({"detail": "Request marked as Under Verification.", "status": request_obj.status}, status=status.HTTP_200_OK)


class SuperAdminVerificationNotesAPIView(APIView):
    """Add or update internal verification notes on a registration request (Super Admin only, never public)."""

    permission_classes = [IsAuthenticated, IsSuperUser]

    def patch(self, request, pk):
        try:
            request_obj = MosqueRegistrationRequest.objects.get(pk=pk)
        except MosqueRegistrationRequest.DoesNotExist:
            return Response({"detail": "Registration request not found."}, status=status.HTTP_404_NOT_FOUND)

        notes = request.data.get("super_admin_notes", "").strip()
        request_obj.super_admin_notes = notes
        request_obj.save(update_fields=["super_admin_notes", "updated_at"])

        from apps.accounts.models import IdentityAuditLog
        IdentityAuditLog.objects.create(
            user=request.user,
            action=IdentityAuditLog.Action.VERIFICATION_NOTES_UPDATED,
            metadata={
                "registration_request_id": request_obj.id,
                "mosque_name": request_obj.mosque_name,
                "updated_by": request.user.username,
            }
        )

        return Response({"detail": "Verification notes updated.", "super_admin_notes": request_obj.super_admin_notes}, status=status.HTTP_200_OK)


class SuperAdminCityListCreateAPIView(generics.ListCreateAPIView):
    """
    List all cities or create a new city.
    Only accessible by Super Admins.
    """
    permission_classes = [IsSuperUser]
    serializer_class = CitySerializer

    def get_queryset(self):
        from apps.locations.models import City
        return City.objects.all().order_by("name")


class SuperAdminCityDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a city.
    Only accessible by Super Admins.
    """
    permission_classes = [IsSuperUser]
    serializer_class = CitySerializer

    def get_queryset(self):
        from apps.locations.models import City
        return City.objects.all()

class SuperAdminCityTimetableAcknowledgeAPIView(APIView):
    """
    Acknowledge missing timetable and continue using existing.
    Accessible by Super Admins.
    """
    permission_classes = [IsSuperUser]

    def post(self, request, pk):
        from apps.locations.models import City
        from django.utils import timezone
        
        try:
            city = City.objects.get(pk=pk)
        except City.DoesNotExist:
            return Response({"detail": "City not found."}, status=status.HTTP_404_NOT_FOUND)
            
        city.acknowledged_timetable_year = timezone.now().year
        city.save(update_fields=['acknowledged_timetable_year'])
        
        return Response({"detail": "Successfully acknowledged."}, status=status.HTTP_200_OK)

class SuperAdminCityTimetableAPIView(APIView):
    """
    Preview and Import city timetable.
    Accessible by Super Admins.
    """
    permission_classes = [IsSuperUser]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, pk, action):
        from apps.locations.models import City, CityDailyPrayerTiming, CityCalendarImportLog
        from apps.platform_admin.services import TimetableParser
        
        if action not in ["preview", "import"]:
            return Response({"detail": "Invalid action. Use preview or import."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            city = City.objects.get(pk=pk)
        except City.DoesNotExist:
            return Response({"detail": "City not found."}, status=status.HTTP_404_NOT_FOUND)
            
        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)
            
        year_str = request.data.get("year")
        if not year_str or not str(year_str).isdigit():
            return Response({"detail": "Valid year is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        year = int(year_str)
        sheet_name = request.data.get("sheet_name")
        if sheet_name == "":
            sheet_name = None
        
        try:
            records, errors, warnings, sheet_names, active_sheet = TimetableParser.parse_file(
                file_obj, year, city.name, sheet_name
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        #=============================================================================

        # except Exception as e:
        #     return Response({"detail": f"Error parsing file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


        except Exception as e:
            print("=" * 80)
            traceback.print_exc()
            print("=" * 80)
            raise

        #=============================================================================
        # Validate duplicates in the parsed records
        dates = [r["date"] for r in records]
        if len(dates) != len(set(dates)):
            errors.append("File contains duplicate dates for the same day.")

        existing_records_count = CityDailyPrayerTiming.objects.filter(
            city=city, 
            date__year=year
        ).count()
        
        overwrite_confirmed = str(request.data.get("overwrite", "false")).lower() == "true"
        import_mode = request.data.get("import_mode", "replace").lower() # replace, merge
        
        if action == "preview":
            return Response({
                "city": city.name,
                "year": year,
                "total_rows": len(records) + len(errors),
                "valid_rows": len(records),
                "invalid_rows": len(errors),
                "warnings": warnings,
                "errors": errors,
                "sheet_names": sheet_names,
                "active_sheet": active_sheet,
                "existing_records_for_year": existing_records_count,
                "requires_overwrite_confirmation": existing_records_count > 0,
                "preview_data": records[:5] + records[-5:] if len(records) > 10 else records
            })
            
        elif action == "import":
            if errors:
                return Response({
                    "detail": "Cannot import file because it contains validation errors.",
                    "errors": errors
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if existing_records_count > 0 and not overwrite_confirmed:
                return Response({
                    "detail": f"Found {existing_records_count} existing records for {year}. Please confirm overwrite resolution."
                }, status=status.HTTP_409_CONFLICT)
            
            from django.db import transaction
            
            try:
                with transaction.atomic():
                    rows_created = 0
                    rows_updated = 0
                    
                    if import_mode == "merge":
                        # Fetch existing timings to merge
                        existing = {
                            obj.date.strftime("%Y-%m-%d"): obj
                            for obj in CityDailyPrayerTiming.objects.filter(city=city, date__year=year)
                        }
                        objects_to_create = []
                        objects_to_update = []
                        
                        for r in records:
                            d_str = r["date"]
                            if d_str in existing:
                                obj = existing[d_str]
                                obj.fajr_time = r["fajr_time"]
                                obj.sunrise_time = r["sunrise_time"]
                                obj.dhuhr_time = r["dhuhr_time"]
                                obj.asr_time = r["asr_time"]
                                obj.maghrib_time = r["maghrib_time"]
                                obj.isha_time = r["isha_time"]
                                objects_to_update.append(obj)
                                rows_updated += 1
                            else:
                                objects_to_create.append(
                                    CityDailyPrayerTiming(
                                        city=city,
                                        date=r["date"],
                                        fajr_time=r["fajr_time"],
                                        sunrise_time=r["sunrise_time"],
                                        dhuhr_time=r["dhuhr_time"],
                                        asr_time=r["asr_time"],
                                        maghrib_time=r["maghrib_time"],
                                        isha_time=r["isha_time"]
                                    )
                                )
                                rows_created += 1
                                
                        if objects_to_create:
                            CityDailyPrayerTiming.objects.bulk_create(objects_to_create, batch_size=500)
                        if objects_to_update:
                            CityDailyPrayerTiming.objects.bulk_update(
                                objects_to_update,
                                fields=["fajr_time", "sunrise_time", "dhuhr_time", "asr_time", "maghrib_time", "isha_time"],
                                batch_size=500
                            )
                    else:
                        # Default is Replace: Delete all and create new
                        CityDailyPrayerTiming.objects.filter(city=city, date__year=year).delete()
                        objects_to_create = [
                            CityDailyPrayerTiming(
                                city=city,
                                date=r["date"],
                                fajr_time=r["fajr_time"],
                                sunrise_time=r["sunrise_time"],
                                dhuhr_time=r["dhuhr_time"],
                                asr_time=r["asr_time"],
                                maghrib_time=r["maghrib_time"],
                                isha_time=r["isha_time"]
                            ) for r in records
                        ]
                        CityDailyPrayerTiming.objects.bulk_create(objects_to_create, batch_size=500)
                        rows_created = len(records)
                    
                    # Log the import
                    CityCalendarImportLog.objects.create(
                        city=city,
                        uploaded_by=request.user,
                        filename=file_obj.name,
                        rows_processed=len(records),
                        rows_created=rows_created,
                        rows_updated=rows_updated,
                        rows_skipped=0
                    )
                    
                msg = f"Successfully imported {len(records)} days of timings for {city.name} ({year}) using {import_mode.capitalize()} resolution."
                return Response({"detail": msg}, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({"detail": f"Database error during import: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SuperAdminCityAdminListCreateAPIView(APIView):
    """
    List all City Admins or create a new City Admin profile.
    Accessible only by Super Admins.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request):
        from apps.accounts.models import CityAdmin
        from apps.platform_admin.serializers import CityAdminSerializer
        city_admins = CityAdmin.objects.select_related("user", "city").all().order_by("-created_at")
        serializer = CityAdminSerializer(city_admins, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        from django.contrib.auth.models import User
        from apps.accounts.models import CityAdmin, IdentityAuditLog, PasswordAuditLog
        from apps.locations.models import City
        from apps.common.utils.strings import normalize_phone_number
        from apps.platform_admin.serializers import CityAdminSerializer
        from rest_framework.exceptions import ValidationError
        from datetime import timedelta
        import string
        import secrets

        mobile_number = request.data.get("mobile_number", "").strip()
        city_id = request.data.get("city_id") or request.data.get("city")
        email = request.data.get("email", "").strip()
        first_name = request.data.get("first_name", "").strip()
        last_name = request.data.get("last_name", "").strip()

        if not mobile_number:
            raise ValidationError({"mobile_number": ["Mobile number is required."]})
        if not city_id:
            raise ValidationError({"city_id": ["City ID is required."]})

        try:
            city_obj = City.objects.get(pk=city_id)
        except City.DoesNotExist:
            raise ValidationError({"city_id": [f"City with ID {city_id} does not exist."]})

        # Rule 3: STRICT ONE ACTIVE CITY ADMIN PER CITY
        if CityAdmin.objects.filter(city=city_obj, is_active=True).exists():
            raise ValidationError({"city_id": [f"City '{city_obj.name}' already has an active City Administrator."]})

        try:
            normalized_mobile = normalize_phone_number(mobile_number)
        except ValueError as e:
            raise ValidationError({"mobile_number": [str(e)]})

        local_digits = normalized_mobile.replace("+91", "")

        existing_user = User.objects.filter(username__in=[normalized_mobile, local_digits]).first()
        if existing_user:
            if CityAdmin.objects.filter(user=existing_user).exists():
                raise ValidationError({"mobile_number": ["A City Admin with this mobile number already exists."]})
            try:
                with transaction.atomic():
                    city_admin = CityAdmin.objects.create(
                        user=existing_user,
                        city=city_obj,
                        mobile_number=normalized_mobile,
                        is_active=True,
                        must_change_password=False,
                    )
                    IdentityAuditLog.objects.create(
                        user=existing_user,
                        action=IdentityAuditLog.Action.CITY_ADMIN_CREATED,
                        metadata={"created_by": request.user.username, "city": city_obj.name, "promoted_existing_user": True}
                    )
            except IntegrityError:
                raise ValidationError({"city_id": [f"City '{city_obj.name}' already has an active City Administrator."]})
            serializer = CityAdminSerializer(city_admin)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if CityAdmin.objects.filter(mobile_number__in=[normalized_mobile, local_digits]).exists():
            raise ValidationError({"mobile_number": ["A City Admin with this mobile number already exists."]})

        # Generate secure temporary password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
        temp_password = ""
        while True:
            temp_password = "".join(secrets.choice(alphabet) for _ in range(14))
            if (any(c.islower() for c in temp_password)
                    and any(c.isupper() for c in temp_password)
                    and any(c.isdigit() for c in temp_password)
                    and any(c in "!@#$%^&*()_+-=" for c in temp_password)):
                break

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=normalized_mobile,
                    email=email,
                    password=temp_password,
                    first_name=first_name,
                    last_name=last_name,
                )
                city_admin = CityAdmin.objects.create(
                    user=user,
                    city=city_obj,
                    mobile_number=normalized_mobile,
                    is_active=True,
                    must_change_password=True,
                    temporary_password_expires_at=timezone.now() + timedelta(days=7),
                )

                IdentityAuditLog.objects.create(
                    user=user,
                    action=IdentityAuditLog.Action.TEMP_PASSWORD_GENERATED,
                    metadata={"created_by": request.user.username, "city": city_obj.name}
                )

                PasswordAuditLog.objects.create(
                    user=user,
                    performed_by=request.user,
                    action=PasswordAuditLog.ActionTypes.GENERATED
                )
        except IntegrityError:
            raise ValidationError({"city_id": [f"City '{city_obj.name}' already has an active City Administrator."]})

        serializer = CityAdminSerializer(city_admin)
        data = serializer.data
        data["temp_password"] = temp_password
        return Response(data, status=status.HTTP_201_CREATED)


class SuperAdminCityAdminDetailAPIView(APIView):
    """
    Retrieve, update or deactivate a City Admin profile.
    Accessible only by Super Admins.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request, pk):
        from apps.accounts.models import CityAdmin
        from apps.platform_admin.serializers import CityAdminSerializer
        try:
            city_admin = CityAdmin.objects.select_related("user", "city").get(pk=pk)
        except CityAdmin.DoesNotExist:
            return Response({"detail": "City Admin not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = CityAdminSerializer(city_admin)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        from apps.accounts.models import CityAdmin
        from apps.locations.models import City
        from apps.platform_admin.serializers import CityAdminSerializer
        from rest_framework.exceptions import ValidationError

        try:
            city_admin = CityAdmin.objects.select_related("user", "city").get(pk=pk)
        except CityAdmin.DoesNotExist:
            return Response({"detail": "City Admin not found."}, status=status.HTTP_404_NOT_FOUND)

        city_id = request.data.get("city_id") or request.data.get("city")
        target_city = city_admin.city
        if city_id is not None:
            try:
                target_city = City.objects.get(pk=city_id)
            except City.DoesNotExist:
                raise ValidationError({"city_id": [f"City with ID {city_id} does not exist."]})

        target_active = city_admin.is_active
        if "is_active" in request.data:
            target_active = bool(request.data["is_active"])

        # Rule 3: STRICT ONE ACTIVE CITY ADMIN PER CITY
        if target_active and CityAdmin.objects.filter(city=target_city, is_active=True).exclude(pk=city_admin.pk).exists():
            raise ValidationError({"city_id": [f"City '{target_city.name}' already has an active City Administrator."]})

        try:
            with transaction.atomic():
                city_admin.city = target_city
                city_admin.is_active = target_active
                city_admin.user.is_active = target_active
                city_admin.user.save(update_fields=["is_active"])

                user = city_admin.user
                if "email" in request.data:
                    user.email = request.data["email"].strip()
                if "first_name" in request.data:
                    user.first_name = request.data["first_name"].strip()
                if "last_name" in request.data:
                    user.last_name = request.data["last_name"].strip()
                user.save()

                city_admin.save()
        except IntegrityError:
            raise ValidationError({"city_id": [f"City '{target_city.name}' already has an active City Administrator."]})

        serializer = CityAdminSerializer(city_admin)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        from apps.accounts.models import CityAdmin
        try:
            city_admin = CityAdmin.objects.get(pk=pk)
        except CityAdmin.DoesNotExist:
            return Response({"detail": "City Admin not found."}, status=status.HTTP_404_NOT_FOUND)

        city_admin.is_active = False
        city_admin.user.is_active = False
        city_admin.user.save(update_fields=["is_active"])
        city_admin.save(update_fields=["is_active", "updated_at"])
        return Response({"detail": "City Admin account deactivated successfully."}, status=status.HTTP_200_OK)


class SuperAdminCityAdminResetPasswordAPIView(APIView):
    """
    Reset temporary password for a City Admin profile.
    Accessible only by Super Admins.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, pk):
        from apps.accounts.models import CityAdmin, PasswordAuditLog
        from rest_framework.authtoken.models import Token
        from datetime import timedelta
        import string
        import secrets

        try:
            city_admin = CityAdmin.objects.select_related("user").get(pk=pk)
        except CityAdmin.DoesNotExist:
            return Response({"detail": "City Admin not found."}, status=status.HTTP_404_NOT_FOUND)

        user = city_admin.user
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
        temp_password = ""
        while True:
            temp_password = "".join(secrets.choice(alphabet) for _ in range(14))
            if (any(c.islower() for c in temp_password)
                    and any(c.isupper() for c in temp_password)
                    and any(c.isdigit() for c in temp_password)
                    and any(c in "!@#$%^&*()_+-=" for c in temp_password)):
                break

        user.set_password(temp_password)
        user.save()

        city_admin.must_change_password = True
        city_admin.temporary_password_expires_at = timezone.now() + timedelta(days=7)
        city_admin.last_password_reset_at = timezone.now()
        city_admin.save()

        PasswordAuditLog.objects.create(
            user=user,
            performed_by=request.user,
            action=PasswordAuditLog.ActionTypes.RESET
        )

        Token.objects.filter(user=user).delete()

        return Response({
            "message": "City Admin password reset successfully.",
            "temp_password": temp_password,
            "username": user.username
        }, status=status.HTTP_200_OK)


class SuperAdminMosqueListAPIView(APIView):
    """
    List all mosques for Super Admin management.
    Supports filtering by status (active, inactive, archived).
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request):
        from apps.mosques.models import Mosque
        status_param = request.query_params.get("status")
        city_id = request.query_params.get("city_id")

        queryset = Mosque.objects.all().select_related("city_relation").order_by("mosque_name")
        if status_param:
            queryset = queryset.filter(mosque_status=status_param)
        if city_id:
            queryset = queryset.filter(city_relation_id=city_id)

        data = []
        for m in queryset:
            data.append({
                "id": m.id,
                "mosque_name": m.mosque_name,
                "city": m.city,
                "city_id": m.city_relation_id,
                "address": m.address,
                "latitude": str(m.latitude) if m.latitude else None,
                "longitude": str(m.longitude) if m.longitude else None,
                "mosque_status": m.mosque_status,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            })
        return Response(data, status=status.HTTP_200_OK)


class SuperAdminMosqueStatusAPIView(APIView):
    """
    Update mosque lifecycle status (active, inactive, archived).
    Accessible only by Super Admins.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def patch(self, request, pk):
        from apps.mosques.models import Mosque
        from apps.accounts.models import MosqueAdmin, IdentityAuditLog

        try:
            mosque = Mosque.objects.get(pk=pk)
        except Mosque.DoesNotExist:
            return Response({"detail": "Mosque not found."}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get("mosque_status")
        if new_status not in [Mosque.MosqueStatus.ACTIVE, Mosque.MosqueStatus.INACTIVE, Mosque.MosqueStatus.ARCHIVED]:
            return Response({"detail": "Invalid mosque status. Must be 'active', 'inactive', or 'archived'."}, status=status.HTTP_400_BAD_REQUEST)

        old_status = mosque.mosque_status
        mosque.mosque_status = new_status
        mosque.save(update_fields=["mosque_status", "updated_at"])

        # Restrict/deactivate or reactivate MosqueAdmin users
        if new_status in [Mosque.MosqueStatus.INACTIVE, Mosque.MosqueStatus.ARCHIVED]:
            admins = MosqueAdmin.objects.filter(mosque=mosque)
            for admin in admins:
                admin.is_active = False
                admin.save(update_fields=["is_active", "updated_at"])
                if not (hasattr(admin.user, "city_admin") and admin.user.city_admin.is_active):
                    admin.user.is_active = False
                    admin.user.save(update_fields=["is_active"])
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
            }
        )

        return Response({
            "detail": f"Mosque status updated from {old_status} to {new_status}.",
            "id": mosque.id,
            "mosque_status": mosque.mosque_status
        }, status=status.HTTP_200_OK)


class SuperAdminMosqueDeleteAPIView(APIView):
    """
    Safely permanently delete a mosque after verifying dependent records.
    Accessible only by Super Admins.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def delete(self, request, pk):
        from apps.mosques.models import Mosque
        from apps.accounts.models import IdentityAuditLog

        try:
            mosque = Mosque.objects.get(pk=pk)
        except Mosque.DoesNotExist:
            return Response({"detail": "Mosque not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check dependent records
        announcements_count = mosque.announcements.count()
        events_count = mosque.events.count()
        admins_count = mosque.admins.count()

        force = request.query_params.get("force") == "true" or request.data.get("force") is True

        if (announcements_count > 0 or events_count > 0 or admins_count > 0) and not force:
            return Response({
                "detail": f"Cannot permanently delete '{mosque.mosque_name}'. It has {announcements_count} announcements, {events_count} events, and {admins_count} assigned admins. Consider archiving the mosque instead.",
                "can_force": True,
                "announcements_count": announcements_count,
                "events_count": events_count,
                "admins_count": admins_count,
            }, status=status.HTTP_400_BAD_REQUEST)

        mosque_name = mosque.mosque_name
        mosque.delete()

        IdentityAuditLog.objects.create(
            user=request.user,
            action=IdentityAuditLog.Action.MOSQUE_DELETED,
            metadata={
                "mosque_id": pk,
                "mosque_name": mosque_name,
                "deleted_by": request.user.username,
                "forced": force,
            }
        )

        return Response({"detail": f"Mosque '{mosque_name}' permanently deleted."}, status=status.HTTP_200_OK)


class SuperAdminCityAdminMobileChangeAPIView(APIView):
    """
    Super Admin initiated lost mobile recovery / number change.
    Dispatches OTP to the new mobile number.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, pk):
        from apps.accounts.models import CityAdmin
        from apps.common.utils.strings import normalize_phone_number
        from django.contrib.auth.models import User
        from rest_framework.exceptions import ValidationError


        try:
            city_admin = CityAdmin.objects.select_related("user").get(pk=pk)
        except CityAdmin.DoesNotExist:
            return Response({"detail": "City Admin not found."}, status=status.HTTP_404_NOT_FOUND)

        new_mobile = request.data.get("new_mobile_number", "").strip()
        reason = request.data.get("reason", "").strip()

        if not new_mobile:
            raise ValidationError({"new_mobile_number": ["New mobile number is required."]})
        if not reason:
            raise ValidationError({"reason": ["Reason for recovery/change is required."]})

        try:
            normalized_mobile = normalize_phone_number(new_mobile)
        except ValueError as e:
            raise ValidationError({"new_mobile_number": [str(e)]})

        local_digits = normalized_mobile.replace("+91", "")

        if User.objects.filter(username__in=[normalized_mobile, local_digits]).exclude(pk=city_admin.user.pk).exists():
            raise ValidationError({"new_mobile_number": ["This mobile number is already assigned to another user."]})
        if CityAdmin.objects.filter(mobile_number__in=[normalized_mobile, local_digits]).exclude(pk=city_admin.pk).exists():
            raise ValidationError({"new_mobile_number": ["This mobile number is already assigned to another City Admin."]})

        force_override = request.data.get("force_override", False) or request.data.get("bypass_otp", False)
        if force_override:
            from apps.accounts.models import IdentityAuditLog, MosqueAdmin
            from rest_framework.authtoken.models import Token
            from django.db import transaction

            old_mobile = city_admin.mobile_number
            with transaction.atomic():
                city_admin.mobile_number = normalized_mobile
                city_admin.save(update_fields=["mobile_number", "updated_at"])

                user = city_admin.user
                if user.username in [old_mobile, old_mobile.replace("+91", "")]:
                    user.username = normalized_mobile
                user.save()

                if hasattr(user, "mosque_admin"):
                    user.mosque_admin.mobile_number = normalized_mobile
                    user.mosque_admin.save(update_fields=["mobile_number", "updated_at"])

                Token.objects.filter(user=user).delete()

                IdentityAuditLog.objects.create(
                    user=request.user,
                    action=IdentityAuditLog.Action.CITY_ADMIN_MOBILE_CHANGED,
                    metadata={
                        "target_city_admin_id": city_admin.id,
                        "target_username": user.username,
                        "old_mobile": old_mobile,
                        "new_mobile": normalized_mobile,
                        "reason": reason,
                        "initiated_by": request.user.username,
                        "forced_override": True,
                    }
                )
            from apps.platform_admin.serializers import CityAdminSerializer
            return Response({
                "detail": f"Registered mobile number successfully updated to {normalized_mobile}.",
                "city_admin": CityAdminSerializer(city_admin).data
            }, status=status.HTTP_200_OK)

        from apps.common.services.otp import OTPService
        result = OTPService.generate_and_send_otp(
            mobile_number=normalized_mobile,
            purpose="account_recovery",
            user=request.user
        )

        if not result.success:
            return Response({"detail": f"Failed to send OTP: {result.message}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "detail": f"OTP sent to new mobile number {normalized_mobile}.",
            "new_mobile_number": normalized_mobile,
            "city_admin_id": city_admin.id
        }, status=status.HTTP_200_OK)


class SuperAdminCityAdminAssignMosqueAPIView(APIView):
    """
    Super Admin endpoint to assign or remove Mosque Admin authority for a City Admin user.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, pk):
        from apps.accounts.models import CityAdmin, MosqueAdmin, IdentityAuditLog
        from apps.mosques.models import Mosque
        from apps.platform_admin.serializers import CityAdminSerializer
        from rest_framework.exceptions import ValidationError
        from django.db import transaction

        try:
            city_admin = CityAdmin.objects.select_related("user", "city").get(pk=pk)
        except CityAdmin.DoesNotExist:
            return Response({"detail": "City Admin not found."}, status=status.HTTP_404_NOT_FOUND)

        mosque_id = request.data.get("mosque_id")

        if mosque_id is None or mosque_id == "" or mosque_id == 0:
            if hasattr(city_admin.user, "mosque_admin"):
                city_admin.user.mosque_admin.delete()
                IdentityAuditLog.objects.create(
                    user=request.user,
                    action="mosque_admin_removed",
                    metadata={
                        "target_user": city_admin.user.username,
                        "removed_by": request.user.username,
                    }
                )
            serializer = CityAdminSerializer(city_admin)
            return Response({
                "detail": "Mosque assignment removed.",
                "city_admin": serializer.data
            }, status=status.HTTP_200_OK)

        try:
            mosque = Mosque.objects.get(pk=mosque_id)
        except Mosque.DoesNotExist:
            raise ValidationError({"mosque_id": [f"Mosque with ID {mosque_id} does not exist."]})

        with transaction.atomic():
            mosque_admin, created = MosqueAdmin.objects.get_or_create(
                user=city_admin.user,
                defaults={
                    "mosque": mosque,
                    "mobile_number": city_admin.mobile_number,
                    "is_active": True,
                }
            )
            if not created:
                mosque_admin.mosque = mosque
                mosque_admin.is_active = True
                mosque_admin.save()

            IdentityAuditLog.objects.create(
                user=request.user,
                action="mosque_admin_assigned",
                metadata={
                    "target_user": city_admin.user.username,
                    "assigned_by": request.user.username,
                    "mosque_id": mosque.id,
                    "mosque_name": mosque.mosque_name,
                }
            )

        serializer = CityAdminSerializer(city_admin)
        return Response({
            "detail": f"Assigned Mosque Admin for '{mosque.mosque_name}'.",
            "city_admin": serializer.data
        }, status=status.HTTP_200_OK)


class SuperAdminCityAdminMobileVerifyAPIView(APIView):
    """
    Super Admin verifies OTP sent to new mobile line, updates number, and invalidates active sessions.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, pk):
        from apps.accounts.models import CityAdmin, IdentityAuditLog
        from apps.common.services.otp import OTPService
        from apps.common.utils.strings import normalize_phone_number
        from rest_framework.authtoken.models import Token
        from rest_framework.exceptions import ValidationError

        try:
            city_admin = CityAdmin.objects.select_related("user", "city").get(pk=pk)
        except CityAdmin.DoesNotExist:
            return Response({"detail": "City Admin not found."}, status=status.HTTP_404_NOT_FOUND)

        new_mobile = request.data.get("new_mobile_number", "").strip()
        otp_code = request.data.get("otp_code", "").strip()

        if not new_mobile or not otp_code:
            raise ValidationError({"detail": "Both new_mobile_number and otp_code are required."})

        try:
            normalized_mobile = normalize_phone_number(new_mobile)
        except ValueError as e:
            raise ValidationError({"new_mobile_number": [str(e)]})

        result = OTPService.verify_otp(
            mobile_number=normalized_mobile,
            otp=otp_code,
            purpose="account_recovery"
        )

        if not result.success:
            return Response({"detail": result.message}, status=status.HTTP_400_BAD_REQUEST)


        with transaction.atomic():
            old_mobile = city_admin.mobile_number
            city_admin.mobile_number = normalized_mobile
            city_admin.save(update_fields=["mobile_number", "updated_at"])

            user = city_admin.user
            if user.username in [old_mobile, old_mobile.replace("+91", "")]:
                user.username = normalized_mobile
            user.save()

            Token.objects.filter(user=user).delete()

            IdentityAuditLog.objects.create(
                user=request.user,
                action=IdentityAuditLog.Action.CITY_ADMIN_MOBILE_CHANGED,
                metadata={
                    "target_city_admin_id": city_admin.id,
                    "target_username": user.username,
                    "old_mobile": old_mobile,
                    "new_mobile": normalized_mobile,
                    "initiated_by": request.user.username,
                    "type": "lost_phone_recovery",
                }
            )

        return Response({
            "detail": f"City Admin mobile number updated to {normalized_mobile}. All active sessions have been invalidated.",
            "city_admin_id": city_admin.id,
            "mobile_number": normalized_mobile
        }, status=status.HTTP_200_OK)


class SuperAdminAccountRecoveryListAPIView(APIView):
    """
    Lists account recovery requests for Super Admin review.
    Requires IsSuperUser.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request):
        from apps.accounts.models import AccountRecoveryRequest
        from apps.platform_admin.serializers import AccountRecoveryRequestSerializer

        status_param = request.query_params.get("status", "").strip().lower()
        queryset = AccountRecoveryRequest.objects.all()

        pending_count = AccountRecoveryRequest.objects.filter(status=AccountRecoveryRequest.Status.PENDING).count()

        if status_param and status_param != "all":
            queryset = queryset.filter(status=status_param)

        serializer = AccountRecoveryRequestSerializer(queryset, many=True)
        return Response({
            "count": queryset.count(),
            "pending_count": pending_count,
            "results": serializer.data,
        }, status=status.HTTP_200_OK)


class SuperAdminAccountRecoveryDetailAPIView(APIView):
    """
    Retrieves detail of a single account recovery request.
    Requires IsSuperUser.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def get(self, request, pk):
        from apps.accounts.models import AccountRecoveryRequest
        from apps.platform_admin.serializers import AccountRecoveryRequestSerializer

        try:
            req_obj = AccountRecoveryRequest.objects.get(pk=pk)
        except AccountRecoveryRequest.DoesNotExist:
            return Response({"detail": "Recovery request not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AccountRecoveryRequestSerializer(req_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SuperAdminAccountRecoveryApproveAPIView(APIView):
    """
    Super Admin approves an account recovery request.
    1. Restores administrator access by updating target user's mobile number.
    2. Updates the registered Mosque's official contact information (contact_phone, contact_email).
    Uses select_for_update() inside atomic transaction for concurrency safety.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, pk):
        from apps.accounts.models import AccountRecoveryRequest, IdentityAuditLog
        from apps.platform_admin.serializers import AccountRecoveryRequestSerializer
        from apps.common.utils.strings import normalize_phone_number
        from django.contrib.auth.models import User
        from django.db import transaction
        from django.utils import timezone
        from rest_framework.authtoken.models import Token

        review_notes = request.data.get("review_notes", "").strip()
        target_user_id = request.data.get("target_user_id")
        custom_mobile = request.data.get("new_mobile_number", "").strip()

        with transaction.atomic():
            try:
                req_obj = AccountRecoveryRequest.objects.select_for_update().get(pk=pk)
            except AccountRecoveryRequest.DoesNotExist:
                return Response({"detail": "Recovery request not found."}, status=status.HTTP_404_NOT_FOUND)

            if req_obj.status != AccountRecoveryRequest.Status.PENDING:
                return Response(
                    {
                        "detail": "This recovery request has already been processed by another Super Admin.",
                        "status": req_obj.status,
                    },
                    status=status.HTTP_409_CONFLICT
                )

            # Authoritative Mosque record
            mosque_obj = req_obj.mosque

            # Stale previous contact verification check:
            # Verify that the mosque's contact number has not changed since the request was created.
            if mosque_obj and req_obj.previous_registered_contact:
                current_contacts = []
                if mosque_obj.contact_phone:
                    try:
                        current_contacts.append(normalize_phone_number(mosque_obj.contact_phone))
                    except ValueError:
                        pass
                else:
                    for admin in mosque_obj.admins.all():
                        try:
                            current_contacts.append(normalize_phone_number(admin.mobile_number))
                        except ValueError:
                            pass

                if req_obj.previous_registered_contact not in current_contacts:
                    return Response(
                        {
                            "detail": "The mosque's registered contact number has changed since this request was submitted. Please re-evaluate the request.",
                        },
                        status=status.HTTP_409_CONFLICT
                    )

            mobile_to_set = custom_mobile or req_obj.contact_whatsapp
            try:
                normalized_mobile = normalize_phone_number(mobile_to_set)
            except ValueError as exc:
                return Response({"new_mobile_number": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

            from django.db.models import Q
            from apps.accounts.models import MosqueAdmin, CityAdmin

            # Target user resolution: Check in order of authoritativeness
            target_user = None
            if target_user_id:
                target_user = User.objects.select_for_update().filter(pk=target_user_id).first()

            if not target_user and req_obj.previous_registered_contact:
                prev_norm = req_obj.previous_registered_contact
                prev_local = prev_norm.replace("+91", "")
                target_user = User.objects.select_for_update().filter(
                    Q(username=prev_norm) | Q(username=prev_local)
                ).first()

                if not target_user:
                    ma = MosqueAdmin.objects.select_related("user").filter(
                        Q(mobile_number=prev_norm) | Q(mobile_number=prev_local)
                    ).first()
                    if ma:
                        target_user = ma.user

                if not target_user:
                    ca = CityAdmin.objects.select_related("user").filter(
                        Q(mobile_number=prev_norm) | Q(mobile_number=prev_local)
                    ).first()
                    if ca:
                        target_user = ca.user

            if not target_user and mosque_obj:
                admin_profile = mosque_obj.admins.select_related("user").first()
                if admin_profile:
                    target_user = admin_profile.user

            if not target_user and req_obj.contact_email:
                target_user = User.objects.select_for_update().filter(email__iexact=req_obj.contact_email).first()

            # MANDATORY CHECK: Target user MUST be found for approval to proceed!
            if not target_user:
                return Response(
                    {"detail": "Target administrator user account could not be found for this recovery request. Please verify the account exists before approving."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 1. Update administrator user & all active role profiles (MosqueAdmin, CityAdmin)
            old_mobile = target_user.username
            target_user.username = normalized_mobile
            target_user.save()

            if hasattr(target_user, "city_admin"):
                ca = target_user.city_admin
                ca.mobile_number = normalized_mobile
                ca.save(update_fields=["mobile_number", "updated_at"])

            if hasattr(target_user, "mosque_admin"):
                ma = target_user.mosque_admin
                ma.mobile_number = normalized_mobile
                ma.save(update_fields=["mobile_number", "updated_at"])

            Token.objects.filter(user=target_user).delete()
            req_obj.target_user = target_user

            # 2. Update official Mosque contact fields
            if mosque_obj:
                mosque_obj.contact_phone = normalized_mobile
                if req_obj.contact_email:
                    mosque_obj.contact_email = req_obj.contact_email
                mosque_obj.save(update_fields=["contact_phone", "contact_email", "updated_at"])

            req_obj.status = AccountRecoveryRequest.Status.APPROVED
            req_obj.reviewed_by = request.user
            req_obj.reviewed_at = timezone.now()
            req_obj.review_notes = review_notes
            req_obj.save()

            IdentityAuditLog.objects.create(
                user=request.user,
                action=IdentityAuditLog.Action.ACCOUNT_RECOVERY_APPROVED,
                metadata={
                    "recovery_request_id": req_obj.id,
                    "approved_by": request.user.username,
                    "target_user_id": target_user.id,
                    "mosque_id": mosque_obj.id if mosque_obj else None,
                    "normalized_mobile": normalized_mobile,
                    "contact_email": req_obj.contact_email,
                    "review_notes": review_notes,
                }
            )

        serializer = AccountRecoveryRequestSerializer(req_obj)
        return Response({
            "detail": f"Account recovery request approved. Administrator identity and official Mosque contact updated to {normalized_mobile}.",
            "request": serializer.data,
        }, status=status.HTTP_200_OK)


class SuperAdminAccountRecoveryRejectAPIView(APIView):
    """
    Super Admin rejects an account recovery request.
    Uses select_for_update() inside atomic transaction for concurrency safety.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, pk):
        from apps.accounts.models import AccountRecoveryRequest, IdentityAuditLog
        from apps.platform_admin.serializers import AccountRecoveryRequestSerializer
        from django.db import transaction
        from django.utils import timezone

        review_notes = request.data.get("review_notes", "").strip()

        with transaction.atomic():
            try:
                req_obj = AccountRecoveryRequest.objects.select_for_update().get(pk=pk)
            except AccountRecoveryRequest.DoesNotExist:
                return Response({"detail": "Recovery request not found."}, status=status.HTTP_404_NOT_FOUND)

            if req_obj.status != AccountRecoveryRequest.Status.PENDING:
                return Response(
                    {
                        "detail": "This recovery request has already been processed by another Super Admin.",
                        "status": req_obj.status,
                    },
                    status=status.HTTP_409_CONFLICT
                )

            req_obj.status = AccountRecoveryRequest.Status.REJECTED
            req_obj.reviewed_by = request.user
            req_obj.reviewed_at = timezone.now()
            req_obj.review_notes = review_notes
            req_obj.save()

            IdentityAuditLog.objects.create(
                user=request.user,
                action=IdentityAuditLog.Action.ACCOUNT_RECOVERY_REJECTED,
                metadata={
                    "recovery_request_id": req_obj.id,
                    "rejected_by": request.user.username,
                    "review_notes": review_notes,
                }
            )

        serializer = AccountRecoveryRequestSerializer(req_obj)
        return Response({
            "detail": "Account recovery request rejected.",
            "request": serializer.data,
        }, status=status.HTTP_200_OK)


class SuperAdminAccountRecoveryReopenAPIView(APIView):
    """
    Super Admin reopens a previously REJECTED account recovery request (REJECTED -> PENDING).
    Uses select_for_update() inside atomic transaction for concurrency safety.
    """
    permission_classes = [IsAuthenticated, IsSuperUser]

    def post(self, request, pk):
        from apps.accounts.models import AccountRecoveryRequest, IdentityAuditLog
        from apps.platform_admin.serializers import AccountRecoveryRequestSerializer
        from django.db import transaction
        from django.utils import timezone

        with transaction.atomic():
            try:
                req_obj = AccountRecoveryRequest.objects.select_for_update().get(pk=pk)
            except AccountRecoveryRequest.DoesNotExist:
                return Response({"detail": "Recovery request not found."}, status=status.HTTP_404_NOT_FOUND)

            if req_obj.status != AccountRecoveryRequest.Status.REJECTED:
                return Response(
                    {
                        "detail": "Only REJECTED recovery requests can be reopened.",
                        "status": req_obj.status,
                    },
                    status=status.HTTP_409_CONFLICT
                )

            req_obj.status = AccountRecoveryRequest.Status.PENDING
            req_obj.reopened_by = request.user
            req_obj.reopened_at = timezone.now()
            req_obj.save()

            IdentityAuditLog.objects.create(
                user=request.user,
                action=IdentityAuditLog.Action.ACCOUNT_RECOVERY_REOPENED,
                metadata={
                    "recovery_request_id": req_obj.id,
                    "reopened_by": request.user.username,
                    "previous_status": "rejected",
                }
            )

        serializer = AccountRecoveryRequestSerializer(req_obj)
        return Response({
            "detail": "Account recovery request has been reopened and returned to the Pending queue.",
            "request": serializer.data,
        }, status=status.HTTP_200_OK)

