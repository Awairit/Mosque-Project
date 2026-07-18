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

        # Check if active MosqueAdmin or CityAdmin profile exists for the given mobile number
        mosque_admin = None
        city_admin = None
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

        res_data = {
            "token": token.key,
            "mobile_number": profile.mobile_number,
            "must_change_password": profile.must_change_password,
            "role": "city_admin" if city_admin else "mosque_admin",
        }
        if mosque_admin:
            res_data["mosque_id"] = mosque_admin.mosque.id
            res_data["mosque_name"] = mosque_admin.mosque.mosque_name
        elif city_admin:
            res_data["city_id"] = city_admin.city.id
            res_data["city_name"] = city_admin.city.name

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
        
        try:
            mosque_admin = request.user.mosque_admin
            mosque_admin.must_change_password = False
            mosque_admin.temporary_password_expires_at = None
            mosque_admin.password_changed_at = timezone.now()
            mosque_admin.save()
        except MosqueAdmin.DoesNotExist:
            try:
                city_admin = request.user.city_admin
                city_admin.must_change_password = False
                city_admin.temporary_password_expires_at = None
                city_admin.password_changed_at = timezone.now()
                city_admin.save()
            except CityAdmin.DoesNotExist:
                pass
            
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
    """Request a password reset OTP."""
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
        try:
            mosque_admin = MosqueAdmin.objects.get(
                Q(mobile_number=normalized) | Q(mobile_number=local_digits)
            )
        except MosqueAdmin.DoesNotExist:
            # Return 200 to prevent user enumeration
            return Response({"detail": "If the number exists, an OTP has been sent."}, status=status.HTTP_200_OK)
            
        from apps.common.services.otp import OTPService
        from apps.common.services.otp_providers import OTPErrorCode
        
        result = OTPService.generate_and_send_otp(
            mobile_number=normalized, 
            purpose="forgot_password",
            user=mosque_admin.user
        )
        
        if not result.success:
            if result.code == OTPErrorCode.RATE_LIMITED:
                return Response({"mobile_number": [result.message]}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            elif result.code in (OTPErrorCode.PROVIDER_UNAVAILABLE, OTPErrorCode.CONFIGURATION_ERROR):
                return Response({"mobile_number": [result.message]}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                return Response({"mobile_number": [result.message]}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"detail": "If the number exists, an OTP has been sent."}, status=status.HTTP_200_OK)

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
        try:
            mosque_admin = MosqueAdmin.objects.get(
                Q(mobile_number=normalized) | Q(mobile_number=local_digits)
            )
        except MosqueAdmin.DoesNotExist:
            return Response({"non_field_errors": ["Invalid request."]}, status=status.HTTP_400_BAD_REQUEST)
            
        from apps.common.services.otp import OTPService
        from apps.common.services.otp_providers import OTPErrorCode
        
        result = OTPService.verify_otp(
            mobile_number=normalized,
            purpose="forgot_password",
            otp=otp,
            user=mosque_admin.user
        )
        
        if not result.success:
            if result.code == OTPErrorCode.RATE_LIMITED:
                return Response({"non_field_errors": [result.message]}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            elif result.code in (OTPErrorCode.PROVIDER_UNAVAILABLE, OTPErrorCode.CONFIGURATION_ERROR):
                return Response({"non_field_errors": [result.message]}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                return Response({"non_field_errors": [result.message]}, status=status.HTTP_400_BAD_REQUEST)
            
        # Invalidate-on-use token payload: "mobile_number:last_changed_timestamp"
        user = mosque_admin.user
        last_changed = mosque_admin.password_changed_at or mosque_admin.last_password_reset_at or user.date_joined
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
        try:
            mosque_admin = MosqueAdmin.objects.get(
                Q(mobile_number=normalized) | Q(mobile_number=local_digits)
            )
        except MosqueAdmin.DoesNotExist:
            return Response({"non_field_errors": ["User not found."]}, status=status.HTTP_400_BAD_REQUEST)
            
        user = mosque_admin.user
        current_changed = mosque_admin.password_changed_at or mosque_admin.last_password_reset_at or user.date_joined
        current_changed_str = str(current_changed.timestamp() if hasattr(current_changed, "timestamp") else current_changed)
        
        # Verify token has not already been used (single-use validation)
        if current_changed_str != last_changed_str:
            return Response({"non_field_errors": ["This reset token has already been used."]}, status=status.HTTP_400_BAD_REQUEST)
            
        user.set_password(new_password)
        user.save()
        
        mosque_admin.must_change_password = False
        mosque_admin.temporary_password_expires_at = None
        mosque_admin.last_password_reset_at = timezone.now()
        mosque_admin.save()
        
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
    """Placeholder endpoint to submit an account recovery request (does not execute db state change but logs audit)."""
    permission_classes = [AllowAny]
    throttle_scope = "sensitive"

    def post(self, request):
        mosque_name = request.data.get("mosque_name", "").strip()
        applicant_name = request.data.get("applicant_name", "").strip()
        contact_email = request.data.get("contact_email", "").strip()
        contact_whatsapp = request.data.get("contact_whatsapp", "").strip()
        notes = request.data.get("notes", "").strip()

        if not mosque_name or not applicant_name or not contact_whatsapp:
            return Response(
                {"non_field_errors": ["Mosque name, applicant name, and WhatsApp number are required."]},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.common.utils.strings import normalize_phone_number
        try:
            normalized_whatsapp = normalize_phone_number(contact_whatsapp)
        except ValueError as exc:
            return Response(
                {"contact_whatsapp": [str(exc)]},
                status=status.HTTP_400_BAD_REQUEST
            )

        from apps.accounts.models import IdentityAuditLog
        IdentityAuditLog.objects.create(
            user=None,
            action=IdentityAuditLog.Action.ACCOUNT_RECOVERY_REQUESTED,
            metadata={
                "mosque_name": mosque_name,
                "applicant_name": applicant_name,
                "contact_email": contact_email,
                "contact_whatsapp": normalized_whatsapp,
                "notes": notes,
            }
        )

        return Response(
            {"detail": "Your Account Recovery request has been submitted. A Super Admin will verify your identity."},
            status=status.HTTP_200_OK
        )
