"""Models for account-related workflows."""

from django.contrib.auth.models import User
from django.db import models

from apps.common.models import TimeStampedModel
from apps.mosques.models import Mosque


class MosqueAdmin(TimeStampedModel):
    """Admin profile for a verified Mosque, linked to a Django User."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="mosque_admin",
    )
    mosque = models.ForeignKey(
        Mosque,
        on_delete=models.CASCADE,
        related_name="admins",
    )
    mobile_number = models.CharField(max_length=32, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    
    # Auth lifecycle
    must_change_password = models.BooleanField(default=False)
    temporary_password_expires_at = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    last_password_reset_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mobile_number", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.mosque.mosque_name}"

class PasswordAuditLog(TimeStampedModel):
    class ActionTypes(models.TextChoices):
        GENERATED = "generated", "Temporary password generated"
        CHANGED = "changed", "Password changed"
        RESET = "reset", "Password reset"
        
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_audit_logs")
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="performed_password_actions")
    action = models.CharField(max_length=32, choices=ActionTypes.choices)
    
    class Meta:
        ordering = ["-created_at"]


class OTPVerification(TimeStampedModel):
    class Purpose(models.TextChoices):
        REGISTRATION = "registration", "Registration"
        FORGOT_PASSWORD = "forgot_password", "Forgot Password"
        LOGIN = "login", "Login"

    mobile_number = models.CharField(max_length=32, db_index=True)
    otp_hash = models.CharField(max_length=128)
    purpose = models.CharField(max_length=32, choices=Purpose.choices)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mobile_number", "purpose", "is_active"]),
        ]

class EmailVerification(TimeStampedModel):
    class Purpose(models.TextChoices):
        REGISTRATION = "registration", "Registration"
        FORGOT_PASSWORD = "forgot_password", "Forgot Password"

    email = models.EmailField(db_index=True)
    token_hash = models.CharField(max_length=128)
    purpose = models.CharField(max_length=32, choices=Purpose.choices)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["email", "purpose", "is_active"]),
        ]

class IdentityAuditLog(TimeStampedModel):
    class Action(models.TextChoices):
        OTP_GENERATED = "otp_generated", "OTP Generated"
        OTP_SENT = "otp_sent", "OTP Sent"
        OTP_VERIFIED = "otp_verified", "OTP Verified"
        OTP_EXPIRED = "otp_expired", "OTP Expired"
        OTP_FAILED = "otp_failed", "OTP Failed"
        EMAIL_SENT = "email_sent", "Email Sent"
        EMAIL_VERIFIED = "email_verified", "Email Verified"
        PASSWORD_CHANGED = "password_changed", "Password Changed"
        PASSWORD_RESET = "password_reset", "Password Reset"
        PASSWORD_RESET_FAILED = "password_reset_failed", "Password Reset Failed"
        TEMP_PASSWORD_GENERATED = "temp_password_generated", "Temporary Password Generated"
        TEMP_PASSWORD_RESET = "temp_password_reset", "Temporary Password Reset"
        LOGIN_FAILED = "login_failed", "Login Failed"
        LOGIN_LOCKED = "login_locked", "Login Locked"
        REGISTRATION_SUBMITTED = "registration_submitted", "Registration Submitted"
        UNDER_VERIFICATION = "under_verification", "Under Verification"
        VERIFICATION_NOTES_UPDATED = "verification_notes_updated", "Verification Notes Updated"
        REGISTRATION_APPROVED = "registration_approved", "Registration Approved"
        REGISTRATION_REJECTED = "registration_rejected", "Registration Rejected"
        ACCOUNT_RECOVERY_REQUESTED = "account_recovery_requested", "Account Recovery Requested"
        FIRST_LOGIN = "first_login", "First Login"
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="identity_audit_logs")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    action = models.CharField(max_length=32, choices=Action.choices)
    status = models.CharField(max_length=32, default="success")
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ["-created_at"]


class CityAdmin(TimeStampedModel):
    """Admin profile for a City, linked to a Django User and assigned to a specific City."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="city_admin",
    )
    city = models.ForeignKey(
        "locations.City",
        on_delete=models.CASCADE,
        related_name="city_admins",
    )
    mobile_number = models.CharField(max_length=32, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    
    # Auth lifecycle
    must_change_password = models.BooleanField(default=False)
    temporary_password_expires_at = models.DateTimeField(null=True, blank=True)
    password_changed_at = models.DateTimeField(null=True, blank=True)
    last_password_reset_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mobile_number", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.city.name}"
