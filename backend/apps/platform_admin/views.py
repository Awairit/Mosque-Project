"""Platform admin API views."""

import secrets
import string
import os
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import models
from django.db import transaction
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
        
#==============================================================================

        print("=== BOOTSTRAP CODE EXECUTED ===")
        
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username=os.environ["BOOTSTRAP_ADMIN_USERNAME"],
                email=os.environ["BOOTSTRAP_ADMIN_EMAIL"],
                password=os.environ["BOOTSTRAP_ADMIN_PASSWORD"],
        )

#==============================================================================
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
        from apps.platform_admin.models import MosqueRegistrationRequest
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
        try:
            request_obj = MosqueRegistrationRequest.objects.get(pk=pk)
        except MosqueRegistrationRequest.DoesNotExist:
            return Response(
                {"detail": "Registration request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        approvable_statuses = [
            MosqueRegistrationRequest.Status.PENDING,
            MosqueRegistrationRequest.Status.UNDER_VERIFICATION,
            MosqueRegistrationRequest.Status.WHATSAPP_VERIFIED,
        ]
        if request_obj.status not in approvable_statuses:
            return Response(
                {"detail": "Only pending or under-verification registration requests can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate 14 character strong temporary password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
        temp_password = ""
        while True:
            temp_password = "".join(secrets.choice(alphabet) for _ in range(14))
            if (any(c.islower() for c in temp_password)
                    and any(c.isupper() for c in temp_password)
                    and any(c.isdigit() for c in temp_password)
                    and any(c in "!@#$%^&*()_+-=" for c in temp_password)):
                break

        from django.contrib.auth.models import User
        from apps.accounts.models import MosqueAdmin, PasswordAuditLog
        from apps.platform_admin.models import MosqueApprovalLog
        from datetime import timedelta

        try:
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

            with transaction.atomic():
                # 1. Create/Get user using mobile number as username
                user, created = User.objects.get_or_create(username=username)
                
                response_password = None
                if created:
                    if email:
                        user.email = email
                    user.set_password(temp_password)
                    user.is_active = True
                    user.save()
                    response_password = temp_password

                # 2. Create Mosque
                google_maps_url = request_obj.google_maps_url or request_obj.google_maps_link
                mosque = Mosque.objects.create(
                    mosque_name=request_obj.mosque_name,
                    city=request_obj.city,
                    city_relation=request_obj.city_relation,
                    address=request_obj.address,
                    google_maps_url=google_maps_url,
                    women_prayer_available=request_obj.women_prayer_available,
                    mosque_status=Mosque.MosqueStatus.ACTIVE,
                )

                # 3. Create MosqueAdmin
                mosque_admin, admin_created = MosqueAdmin.objects.get_or_create(
                    user=user,
                    defaults={
                        "mosque": mosque,
                        "mobile_number": request_obj.mobile_number,
                        "is_active": True,
                    }
                )
                
                if created:
                    mosque_admin.must_change_password = True
                    mosque_admin.temporary_password_expires_at = timezone.now() + timedelta(days=7)
                    mosque_admin.save()
                    
                    PasswordAuditLog.objects.create(
                        user=user,
                        performed_by=request.user,
                        action=PasswordAuditLog.ActionTypes.GENERATED
                    )

                # 4. Mark request as Approved
                request_obj.status = MosqueRegistrationRequest.Status.APPROVED
                request_obj.approved_by = request.user
                request_obj.approved_at = timezone.now()
                request_obj.save()

                # 5. Create audit records
                MosqueApprovalLog.objects.create(
                    action=MosqueApprovalLog.ActionTypes.APPROVE,
                    mosque=mosque,
                    registration_request_id=request_obj.id,
                    mosque_name=request_obj.mosque_name,
                    admin=request.user,
                )

                from apps.accounts.models import IdentityAuditLog
                IdentityAuditLog.objects.create(
                    user=request.user,
                    action=IdentityAuditLog.Action.REGISTRATION_APPROVED,
                    metadata={
                        "registration_request_id": request_obj.id,
                        "mosque_name": request_obj.mosque_name,
                        "approved_by": request.user.username,
                    }
                )
                if created:
                    IdentityAuditLog.objects.create(
                        user=user,
                        action=IdentityAuditLog.Action.TEMP_PASSWORD_GENERATED,
                        metadata={
                            "generated_by": request.user.username,
                            "expiry": str(mosque_admin.temporary_password_expires_at)
                        }
                    )
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
        try:
            request_obj = MosqueRegistrationRequest.objects.get(pk=pk)
        except MosqueRegistrationRequest.DoesNotExist:
            return Response(
                {"detail": "Registration request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        rejectable_statuses = [
            MosqueRegistrationRequest.Status.PENDING,
            MosqueRegistrationRequest.Status.UNDER_VERIFICATION,
            MosqueRegistrationRequest.Status.WHATSAPP_VERIFIED,
        ]
        if request_obj.status not in rejectable_statuses:
            return Response(
                {"detail": "This registration request cannot be rejected in its current state."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get("reason", "").strip()
        if not reason:
            return Response(
                {"reason": ["Rejection reason is required."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.platform_admin.models import MosqueApprovalLog

        try:
            with transaction.atomic():
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

                from apps.accounts.models import IdentityAuditLog
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
