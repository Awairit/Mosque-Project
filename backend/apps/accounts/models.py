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
        ACCOUNT_RECOVERY_VERIFICATION_FAILED = "account_recovery_verification_failed", "Account Recovery Verification Failed"
        ACCOUNT_RECOVERY_APPROVED = "account_recovery_approved", "Account Recovery Approved"
        ACCOUNT_RECOVERY_REJECTED = "account_recovery_rejected", "Account Recovery Rejected"
        ACCOUNT_RECOVERY_REOPENED = "account_recovery_reopened", "Account Recovery Reopened"
        FIRST_LOGIN = "first_login", "First Login"
        CITY_ADMIN_CREATED = "city_admin_created", "City Admin Created"
        CITY_ADMIN_STATUS_CHANGED = "city_admin_status_changed", "City Admin Status Changed"
        CITY_ADMIN_MOBILE_CHANGED = "city_admin_mobile_changed", "City Admin Mobile Changed"
        CITY_ADMIN_PASSWORD_RESET = "city_admin_password_reset", "City Admin Password Reset"
        MOSQUE_STATUS_CHANGED = "mosque_status_changed", "Mosque Status Changed"
        MOSQUE_DELETED = "mosque_deleted", "Mosque Deleted"

    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="identity_audit_logs")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    action = models.CharField(max_length=48, choices=Action.choices)
    status = models.CharField(max_length=32, default="success")
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ["-created_at"]


class AccountRecoveryRequest(TimeStampedModel):
    """Manual account recovery request submitted by a user who lost access."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    mosque = models.ForeignKey(
        "mosques.Mosque",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="account_recovery_requests",
    )
    mosque_name = models.CharField(max_length=255)
    applicant_name = models.CharField(max_length=255)
    previous_registered_contact = models.CharField(max_length=32, blank=True)
    contact_email = models.CharField(max_length=254, blank=True)
    contact_whatsapp = models.CharField(max_length=32)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_recovery_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    reopened_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reopened_recovery_requests",
    )
    reopened_at = models.DateTimeField(null=True, blank=True)
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="account_recovery_requests",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Recovery Request #{self.id} - {self.applicant_name} ({self.mosque_name})"


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
        constraints = [
            models.UniqueConstraint(
                fields=["city"],
                condition=models.Q(is_active=True),
                name="unique_active_city_admin_per_city",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.city.name}"
