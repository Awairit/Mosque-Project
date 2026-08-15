"""API views for account-related workflows."""

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

from apps.accounts.permissions import IsCityAdmin
from apps.accounts.models import MosqueAdmin, CityAdmin
from apps.accounts.serializers import LoginSerializer


class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "sensitive"

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        mobile_number = serializer.validated_data["mobile_number"]
        password = serializer.validated_data["password"]

        # Normalize phone number to match database profiles (supporting fallback)
        from apps.common.utils.strings import normalize_phone_number
        try:
            normalized = normalize_phone_number(mobile_number)
        except ValueError:
            normalized = mobile_number

        local_digits = normalized.replace("+91", "")

        # First check if this is a Super Admin login attempt by username or email
        from django.contrib.auth.models import User
        try:
            potential_super = User.objects.get(Q(username=mobile_number) | Q(email=mobile_number))
            if potential_super.is_superuser:
                user = authenticate(username=potential_super.username, password=password)
                if user and user.is_superuser and user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    return Response({
                        "token": token.key,
                        "username": user.username,
                        "email": user.email,
                        "role": "super_admin",
                        "must_change_password": False,
                    }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            pass

        # Check if user exists by username (E.164 normalized or local digits) or by role profile mobile_number
        user_by_username = User.objects.filter(
            Q(username=normalized) | Q(username=local_digits)
        ).first()

        profile = None
        mosque_admin = None
        city_admin = None

        if user_by_username:
            if hasattr(user_by_username, "mosque_admin") and user_by_username.mosque_admin.is_active:
                mosque_admin = user_by_username.mosque_admin
                profile = mosque_admin
            elif hasattr(user_by_username, "city_admin") and user_by_username.city_admin.is_active:
                city_admin = user_by_username.city_admin
                profile = city_admin

        if not profile:
            try:
                mosque_admin = MosqueAdmin.objects.select_related(
                    "user", "mosque"
                ).get(Q(mobile_number=normalized) | Q(mobile_number=local_digits))
                profile = mosque_admin
            except MosqueAdmin.DoesNotExist:
                try:
                    city_admin = CityAdmin.objects.select_related(
                        "user", "city"
                    ).get(Q(mobile_number=normalized) | Q(mobile_number=local_digits))
                    profile = city_admin
                except CityAdmin.DoesNotExist:
                    return Response(
                        {"non_field_errors": ["Invalid mobile number or password."]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        if not profile.is_active or not profile.user.is_active:
            return Response(
                {"non_field_errors": ["This account has been disabled."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Authenticate the user. Username is user's username (avoids E.164 mismatch).
        user = authenticate(username=profile.user.username, password=password)
        if not user:
            return Response(
                {"non_field_errors": ["Invalid mobile number or password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Evaluate all active role profiles linked to this user
        has_city_admin = hasattr(user, "city_admin") and user.city_admin.is_active
        has_mosque_admin = (
            hasattr(user, "mosque_admin")
            and user.mosque_admin.is_active
            and user.mosque_admin.mosque
            and user.mosque_admin.mosque.mosque_status not in ["inactive", "archived"]
        )

        if not has_city_admin and not has_mosque_admin:
            return Response(
                {"non_field_errors": ["Account access is disabled because the associated profile or mosque is inactive."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if temporary password has expired
        if profile.must_change_password and profile.temporary_password_expires_at:
             if timezone.now() > profile.temporary_password_expires_at:
                return Response(
                    {"non_field_errors": ["Your temporary password has expired. Please contact Super Admin to reset it."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        token, _ = Token.objects.get_or_create(user=user)

        # Log first login / audit log
        from apps.accounts.models import IdentityAuditLog
        if profile.must_change_password:
            IdentityAuditLog.objects.create(
                user=user,
                action=IdentityAuditLog.Action.FIRST_LOGIN,
                metadata={"username": mobile_number}
            )

        roles = []
        if has_city_admin:
            roles.append("city_admin")
        if has_mosque_admin:
            roles.append("mosque_admin")

        primary_role = roles[0] if roles else ("city_admin" if city_admin else "mosque_admin")

        res_data = {
            "token": token.key,
            "mobile_number": profile.mobile_number,
            "must_change_password": profile.must_change_password,
            "role": primary_role,
            "roles": roles,
        }

        if has_city_admin:
            res_data["city_id"] = user.city_admin.city.id
            res_data["city_name"] = user.city_admin.city.name
            res_data["city"] = {
                "id": user.city_admin.city.id,
                "name": user.city_admin.city.name,
            }

        if has_mosque_admin:
            res_data["mosque_id"] = user.mosque_admin.mosque.id
            res_data["mosque_name"] = user.mosque_admin.mosque.mosque_name
            res_data["mosque"] = {
                "id": user.mosque_admin.mosque.id,
                "name": user.mosque_admin.mosque.mosque_name,
            }

        return Response(res_data, status=status.HTTP_200_OK)



class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.accounts.models import PasswordAuditLog
        
        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        
        if not current_password or not new_password:
            return Response({"non_field_errors": ["Both current and new passwords are required."]}, status=status.HTTP_400_BAD_REQUEST)
            
        if not request.user.check_password(current_password):
            return Response({"current_password": ["Invalid current password."]}, status=status.HTTP_400_BAD_REQUEST)
            
        if len(new_password) < 8:
            return Response({"new_password": ["Password must be at least 8 characters long."]}, status=status.HTTP_400_BAD_REQUEST)
            
        request.user.set_password(new_password)
        request.user.save()
        
        now = timezone.now()
        
        # Synchronize password flags across all attached role profiles for dual-role users (BUG-004)
        if hasattr(request.user, "mosque_admin") and request.user.mosque_admin:
            mosque_admin = request.user.mosque_admin
            mosque_admin.must_change_password = False
            mosque_admin.temporary_password_expires_at = None
            mosque_admin.password_changed_at = now
            mosque_admin.save(update_fields=["must_change_password", "temporary_password_expires_at", "password_changed_at", "updated_at"])

        if hasattr(request.user, "city_admin") and request.user.city_admin:
            city_admin = request.user.city_admin
            city_admin.must_change_password = False
            city_admin.temporary_password_expires_at = None
            city_admin.password_changed_at = now
            city_admin.save(update_fields=["must_change_password", "temporary_password_expires_at", "password_changed_at", "updated_at"])
            
        PasswordAuditLog.objects.create(
            user=request.user,
            performed_by=request.user,
            action=PasswordAuditLog.ActionTypes.CHANGED
        )

        from apps.accounts.models import IdentityAuditLog
        IdentityAuditLog.objects.create(
            user=request.user,
            action=IdentityAuditLog.Action.PASSWORD_CHANGED,
            metadata={"source": "change_password_api"}
        )
        
        return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)

class ForgotPasswordRequestAPIView(APIView):
    """Request a password reset OTP for registered accounts."""
    permission_classes = [AllowAny]
    throttle_scope = "sensitive"
    
    def post(self, request):
        mobile_number = request.data.get("mobile_number")
        
        if not mobile_number:
            return Response({"mobile_number": ["Mobile number is required."]}, status=status.HTTP_400_BAD_REQUEST)
            
        from apps.common.utils.strings import normalize_phone_number
        try:
            normalized = normalize_phone_number(mobile_number)
        except ValueError as exc:
            return Response({"mobile_number": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        local_digits = normalized.replace("+91", "")
        from django.contrib.auth.models import User

        # Check account existence across User.username, MosqueAdmin, and CityAdmin
        user = User.objects.filter(Q(username=normalized) | Q(username=local_digits)).first()

        if not user:
            ma = MosqueAdmin.objects.filter(Q(mobile_number=normalized) | Q(mobile_number=local_digits)).first()
            if ma:
                user = ma.user

        if not user:
            ca = CityAdmin.objects.filter(Q(mobile_number=normalized) | Q(mobile_number=local_digits)).first()
            if ca:
                user = ca.user

        # Strict validation: If account does NOT exist, stop immediately with HTTP 400
        if not user:
            return Response(
                {"mobile_number": ["Account not found. No Mosque Finder account is registered with this phone number. Please check the number and try again."]},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        from apps.common.services.otp import OTPService
        from apps.common.services.otp_providers import OTPErrorCode
        
        result = OTPService.generate_and_send_otp(
            mobile_number=normalized, 
            purpose="forgot_password",
            user=user
        )
        
        if not result.success:
            if result.code == OTPErrorCode.RATE_LIMITED:
                return Response({"mobile_number": [result.message]}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            elif result.code in (OTPErrorCode.PROVIDER_UNAVAILABLE, OTPErrorCode.CONFIGURATION_ERROR):
                return Response({"mobile_number": [result.message]}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                return Response({"mobile_number": [result.message]}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"detail": "An OTP has been sent to your registered phone number."}, status=status.HTTP_200_OK)


class ForgotPasswordVerifyAPIView(APIView):
    """Verify the OTP for password reset."""
    permission_classes = [AllowAny]
    throttle_scope = "sensitive"
    
    def post(self, request):
        mobile_number = request.data.get("mobile_number")
        otp = request.data.get("otp")
        
        if not mobile_number or not otp:
            return Response({"non_field_errors": ["Mobile number and OTP are required."]}, status=status.HTTP_400_BAD_REQUEST)
            
        from apps.common.utils.strings import normalize_phone_number
        try:
            normalized = normalize_phone_number(mobile_number)
        except ValueError as exc:
            return Response({"non_field_errors": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        local_digits = normalized.replace("+91", "")
        profile = None
        try:
            mosque_admin = MosqueAdmin.objects.get(
                Q(mobile_number=normalized) | Q(mobile_number=local_digits)
            )
            profile = mosque_admin
        except MosqueAdmin.DoesNotExist:
            try:
                city_admin = CityAdmin.objects.get(
                    Q(mobile_number=normalized) | Q(mobile_number=local_digits)
                )
                profile = city_admin
            except CityAdmin.DoesNotExist:
                return Response({"non_field_errors": ["Invalid request."]}, status=status.HTTP_400_BAD_REQUEST)
            
        from apps.common.services.otp import OTPService
        from apps.common.services.otp_providers import OTPErrorCode
        
        user = profile.user
        result = OTPService.verify_otp(
            mobile_number=normalized,
            purpose="forgot_password",
            otp=otp,
            user=user
        )
        
        if not result.success:
            if result.code == OTPErrorCode.RATE_LIMITED:
                return Response({"non_field_errors": [result.message]}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            elif result.code in (OTPErrorCode.PROVIDER_UNAVAILABLE, OTPErrorCode.CONFIGURATION_ERROR):
                return Response({"non_field_errors": [result.message]}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                return Response({"non_field_errors": [result.message]}, status=status.HTTP_400_BAD_REQUEST)
            
        # Invalidate-on-use token payload: "mobile_number:last_changed_timestamp"
        last_changed = profile.password_changed_at or profile.last_password_reset_at or user.date_joined
        last_changed_str = str(last_changed.timestamp() if hasattr(last_changed, "timestamp") else last_changed)
        
        payload = f"{normalized}:{last_changed_str}"
        
        from django.core.signing import TimestampSigner
        signer = TimestampSigner()
        reset_token = signer.sign(payload)
        
        return Response({
            "detail": "OTP verified successfully.",
            "reset_token": reset_token
        }, status=status.HTTP_200_OK)


class ForgotPasswordResetAPIView(APIView):
    """Reset the password using the verified token."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        reset_token = request.data.get("reset_token")
        new_password = request.data.get("new_password")
        
        if not reset_token or not new_password:
            return Response({"non_field_errors": ["Reset token and new password are required."]}, status=status.HTTP_400_BAD_REQUEST)
            
        if len(new_password) < 8:
            return Response({"new_password": ["Password must be at least 8 characters long."]}, status=status.HTTP_400_BAD_REQUEST)
            
        from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
        signer = TimestampSigner()
        
        try:
            # Token valid for 15 minutes
            payload = signer.unsign(reset_token, max_age=900)
            if ":" not in payload:
                return Response({"non_field_errors": ["Invalid reset token."]}, status=status.HTTP_400_BAD_REQUEST)
            mobile_number, last_changed_str = payload.rsplit(":", 1)
            from apps.common.utils.strings import normalize_phone_number
            normalized = normalize_phone_number(mobile_number)
        except (BadSignature, SignatureExpired, ValueError):
            return Response({"non_field_errors": ["Invalid or expired reset token."]}, status=status.HTTP_400_BAD_REQUEST)
            
        local_digits = normalized.replace("+91", "")
        profile = None
        try:
            mosque_admin = MosqueAdmin.objects.get(
                Q(mobile_number=normalized) | Q(mobile_number=local_digits)
            )
            profile = mosque_admin
        except MosqueAdmin.DoesNotExist:
            try:
                city_admin = CityAdmin.objects.get(
                    Q(mobile_number=normalized) | Q(mobile_number=local_digits)
                )
                profile = city_admin
            except CityAdmin.DoesNotExist:
                return Response({"non_field_errors": ["User not found."]}, status=status.HTTP_400_BAD_REQUEST)
            
        user = profile.user
        current_changed = profile.password_changed_at or profile.last_password_reset_at or user.date_joined
        current_changed_str = str(current_changed.timestamp() if hasattr(current_changed, "timestamp") else current_changed)
        
        # Verify token has not already been used (single-use validation)
        if current_changed_str != last_changed_str:
            return Response({"non_field_errors": ["This reset token has already been used."]}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.save()
        
        now = timezone.now()
        if hasattr(user, "mosque_admin") and user.mosque_admin:
            m_admin = user.mosque_admin
            m_admin.must_change_password = False
            m_admin.temporary_password_expires_at = None
            m_admin.last_password_reset_at = now
            m_admin.save(update_fields=["must_change_password", "temporary_password_expires_at", "last_password_reset_at", "updated_at"])

        if hasattr(user, "city_admin") and user.city_admin:
            c_admin = user.city_admin
            c_admin.must_change_password = False
            c_admin.temporary_password_expires_at = None
            c_admin.last_password_reset_at = now
            c_admin.save(update_fields=["must_change_password", "temporary_password_expires_at", "last_password_reset_at", "updated_at"])
        
        # Invalidate existing sessions
        Token.objects.filter(user=user).delete()
        
        from apps.accounts.models import IdentityAuditLog
        IdentityAuditLog.objects.create(
            user=user,
            action=IdentityAuditLog.Action.PASSWORD_RESET,
            metadata={"mobile_number": normalized}
        )
        
        return Response({"detail": "Password reset successfully. Please login with your new password."}, status=status.HTTP_200_OK)



class AccountRecoveryRequestAPIView(APIView):
    """Submits and persists an account recovery request for Super Admin manual review."""
    permission_classes = [AllowAny]
    throttle_scope = "sensitive"

    def post(self, request):
        mosque_id = request.data.get("mosque_id")
        mosque_name = request.data.get("mosque_name", "").strip()
        applicant_name = request.data.get("applicant_name", "").strip()
        previous_registered_contact = request.data.get("previous_registered_contact", "").strip()
        contact_email = request.data.get("contact_email", "").strip()
        contact_whatsapp = request.data.get("contact_whatsapp", "").strip()
        notes = request.data.get("notes", "").strip()

        if not applicant_name or not previous_registered_contact or not contact_whatsapp or (not mosque_id and not mosque_name):
            return Response(
                {"non_field_errors": ["Mosque selection/name, applicant name, previous registered contact, and new WhatsApp number are required."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.common.utils.strings import normalize_phone_number
        try:
            normalized_previous = normalize_phone_number(previous_registered_contact)
        except ValueError as exc:
            return Response(
                {"previous_registered_contact": [str(exc)]},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            normalized_whatsapp = normalize_phone_number(contact_whatsapp)
        except ValueError as exc:
            return Response(
                {"contact_whatsapp": [str(exc)]},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Resolve against registered active Mosque database
        from apps.mosques.models import Mosque
        mosque_obj = None
        if mosque_id:
            mosque_obj = Mosque.objects.filter(id=mosque_id, mosque_status=Mosque.MosqueStatus.ACTIVE).first()
        if not mosque_obj and mosque_name:
            mosque_obj = Mosque.objects.filter(mosque_name__iexact=mosque_name, mosque_status=Mosque.MosqueStatus.ACTIVE).first()

        if not mosque_obj:
            return Response(
                {"mosque_name": ["This mosque is not registered on Mosque Finder. Account recovery is only available for registered mosques."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Stage 1 Security Check: Verify previous registered contact number
        from apps.accounts.models import AccountRecoveryRequest, IdentityAuditLog
        authoritative_contacts = []
        if mosque_obj.contact_phone:
            try:
                authoritative_contacts.append(normalize_phone_number(mosque_obj.contact_phone))
            except ValueError:
                pass
        else:
            # Check MosqueAdmin mobile numbers linked to this mosque as fallback
            for admin in mosque_obj.admins.all():
                try:
                    authoritative_contacts.append(normalize_phone_number(admin.mobile_number))
                except ValueError:
                    pass

        if normalized_previous not in authoritative_contacts:
            IdentityAuditLog.objects.create(
                user=None,
                action=IdentityAuditLog.Action.ACCOUNT_RECOVERY_VERIFICATION_FAILED,
                metadata={
                    "mosque_id": mosque_obj.id,
                    "mosque_name": mosque_obj.mosque_name,
                    "applicant_name": applicant_name,
                    "reason": "Previous registered contact mismatch",
                }
            )
            return Response(
                {"previous_registered_contact": ["Previous registered contact number does not match our records. Please verify the number currently registered for this mosque."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        recovery_req = AccountRecoveryRequest.objects.create(
            mosque=mosque_obj,
            mosque_name=mosque_obj.mosque_name,
            applicant_name=applicant_name,
            previous_registered_contact=normalized_previous,
            contact_email=contact_email,
            contact_whatsapp=normalized_whatsapp,
            notes=notes,
            status=AccountRecoveryRequest.Status.PENDING,
        )

        IdentityAuditLog.objects.create(
            user=None,
            action=IdentityAuditLog.Action.ACCOUNT_RECOVERY_REQUESTED,
            metadata={
                "recovery_request_id": recovery_req.id,
                "mosque_id": mosque_obj.id,
                "mosque_name": mosque_obj.mosque_name,
                "applicant_name": applicant_name,
                "previous_registered_contact": normalized_previous,
                "contact_email": contact_email,
                "contact_whatsapp": normalized_whatsapp,
                "notes": notes,
            }
        )

        return Response(
            {
                "detail": "Your Account Recovery request has been submitted. A Super Admin will verify your identity.",
                "id": recovery_req.id,
            },
            status=status.HTTP_201_CREATED
        )


class CityAdminProfileAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCityAdmin]

    def get(self, request):
        city_admin = request.user.city_admin
        user = request.user
        has_mosque_admin = (
            hasattr(user, "mosque_admin")
            and user.mosque_admin.is_active
            and user.mosque_admin.mosque
            and user.mosque_admin.mosque.mosque_status not in ["inactive", "archived"]
        )

        roles = ["city_admin"]
        if has_mosque_admin:
            roles.append("mosque_admin")

        res_data = {
            "id": city_admin.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "mobile_number": city_admin.mobile_number,
            "city_id": city_admin.city.id,
            "city_name": city_admin.city.name,
            "is_active": city_admin.is_active,
            "must_change_password": city_admin.must_change_password,
            "created_at": city_admin.created_at.isoformat() if city_admin.created_at else None,
            "roles": roles,
            "has_mosque_admin": bool(has_mosque_admin),
        }

        if has_mosque_admin:
            res_data["mosque_id"] = user.mosque_admin.mosque.id
            res_data["mosque_name"] = user.mosque_admin.mosque.mosque_name

        return Response(res_data, status=status.HTTP_200_OK)

    def patch(self, request):
        city_admin = request.user.city_admin
        user = request.user

        for field in ["city", "city_id", "is_active", "role"]:
            if field in request.data:
                return Response(
                    {"detail": f"Field '{field}' cannot be modified by City Admin. Contact Super Admin."},
                    status=status.HTTP_403_FORBIDDEN
                )

        if "first_name" in request.data:
            user.first_name = request.data["first_name"].strip()
        if "last_name" in request.data:
            user.last_name = request.data["last_name"].strip()
        if "email" in request.data:
            user.email = request.data["email"].strip()

        user.save()
        return Response({
            "detail": "Profile updated successfully.",
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
        }, status=status.HTTP_200_OK)


class CityAdminChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCityAdmin]

    def post(self, request):
        user = request.user
        city_admin = user.city_admin

        current_password = request.data.get("current_password", "")
        new_password = request.data.get("new_password", "")
        confirm_password = request.data.get("confirm_password", "")

        if not current_password or not new_password or not confirm_password:
            return Response({"detail": "All password fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({"current_password": ["Incorrect current password."]}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({"confirm_password": ["New password and confirmation do not match."]}, status=status.HTTP_400_BAD_REQUEST)

        if len(new_password) < 8:
            return Response({"new_password": ["Password must be at least 8 characters long."]}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        city_admin.must_change_password = False
        city_admin.password_changed_at = timezone.now()
        city_admin.save(update_fields=["must_change_password", "password_changed_at", "updated_at"])

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        from apps.accounts.models import IdentityAuditLog
        IdentityAuditLog.objects.create(
            user=user,
            action=IdentityAuditLog.Action.PASSWORD_CHANGED,
            metadata={"changed_by": user.username, "role": "city_admin"}
        )

        return Response({
            "detail": "Password changed successfully.",
            "token": token.key
        }, status=status.HTTP_200_OK)


class CityAdminMobileChangeRequestAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCityAdmin]

    def post(self, request):
        user = request.user
        city_admin = user.city_admin

        current_password = request.data.get("current_password", "")
        new_mobile = request.data.get("new_mobile_number", "").strip()

        if not current_password or not new_mobile:
            return Response({"detail": "Current password and new mobile number are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(current_password):
            return Response({"current_password": ["Incorrect current password."]}, status=status.HTTP_400_BAD_REQUEST)

        from apps.common.utils.strings import normalize_phone_number
        try:
            normalized_mobile = normalize_phone_number(new_mobile)
        except ValueError as exc:
            return Response({"new_mobile_number": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        local_digits = normalized_mobile.replace("+91", "")

        from django.contrib.auth.models import User
        if User.objects.filter(username__in=[normalized_mobile, local_digits]).exclude(pk=user.pk).exists():
            return Response({"new_mobile_number": ["This mobile number is already in use by another user."]}, status=status.HTTP_400_BAD_REQUEST)
        if CityAdmin.objects.filter(mobile_number__in=[normalized_mobile, local_digits]).exclude(pk=city_admin.pk).exists():
            return Response({"new_mobile_number": ["This mobile number is already in use by another City Admin."]}, status=status.HTTP_400_BAD_REQUEST)

        from apps.common.services.otp import OTPService
        result = OTPService.generate_and_send_otp(
            mobile_number=normalized_mobile,
            purpose="account_recovery",
            user=user
        )


        if not result.success:
            return Response({"detail": f"Failed to send OTP: {result.message}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "detail": f"OTP sent to new mobile number {normalized_mobile}.",
            "new_mobile_number": normalized_mobile
        }, status=status.HTTP_200_OK)


class CityAdminMobileChangeVerifyAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCityAdmin]

    def post(self, request):
        user = request.user
        city_admin = user.city_admin

        new_mobile = request.data.get("new_mobile_number", "").strip()
        otp_code = request.data.get("otp_code", "").strip()

        if not new_mobile or not otp_code:
            return Response({"detail": "Both new_mobile_number and otp_code are required."}, status=status.HTTP_400_BAD_REQUEST)

        from apps.common.utils.strings import normalize_phone_number
        try:
            normalized_mobile = normalize_phone_number(new_mobile)
        except ValueError as exc:
            return Response({"new_mobile_number": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        from apps.common.services.otp import OTPService
        result = OTPService.verify_otp(
            mobile_number=normalized_mobile,
            otp=otp_code,
            purpose="account_recovery"
        )

        if not result.success:
            return Response({"detail": result.message}, status=status.HTTP_400_BAD_REQUEST)


        old_mobile = city_admin.mobile_number
        city_admin.mobile_number = normalized_mobile
        city_admin.save(update_fields=["mobile_number", "updated_at"])

        if user.username in [old_mobile, old_mobile.replace("+91", "")]:
            user.username = normalized_mobile
            user.save()

        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        from apps.accounts.models import IdentityAuditLog
        IdentityAuditLog.objects.create(
            user=user,
            action=IdentityAuditLog.Action.CITY_ADMIN_MOBILE_CHANGED,
            metadata={
                "old_mobile": old_mobile,
                "new_mobile": normalized_mobile,
                "changed_by": user.username,
                "type": "self_service",
            }
        )

        return Response({
            "detail": "Mobile number updated successfully.",
            "mobile_number": normalized_mobile,
            "token": token.key
        }, status=status.HTTP_200_OK)

