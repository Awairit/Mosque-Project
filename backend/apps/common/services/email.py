"""Email Verification Service."""

import uuid
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from apps.accounts.models import EmailVerification, IdentityAuditLog
from apps.common.services.notification import notification_service

class EmailVerificationService:
    """Service to handle generation, sending, and verification of email links."""
    
    EXPIRY_HOURS = 24
    
    @classmethod
    def _generate_token(cls) -> str:
        """Generate a secure random token."""
        return uuid.uuid4().hex
        
    @classmethod
    def generate_and_send_link(cls, email: str, purpose: str, user=None) -> bool:
        """Generate a new email verification token, save it, and send it."""
        # Invalidate existing active tokens for this email and purpose
        EmailVerification.objects.filter(
            email=email,
            purpose=purpose,
            is_active=True
        ).update(is_active=False)
        
        token = cls._generate_token()
        token_hash = make_password(token)
        expires_at = timezone.now() + timedelta(hours=cls.EXPIRY_HOURS)
        
        EmailVerification.objects.create(
            email=email,
            token_hash=token_hash,
            purpose=purpose,
            expires_at=expires_at,
        )
        
        # Log generation
        IdentityAuditLog.objects.create(
            user=user,
            action=IdentityAuditLog.Action.OTP_GENERATED, # Re-use action or add EMAIL_TOKEN_GENERATED
            metadata={"email": email, "purpose": purpose}
        )
        
        # Send Email
        # In a real application, we would use reverse() to build a full URL.
        # Assuming frontend domain is provided via settings.FRONTEND_URL
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        verification_link = f"{frontend_url}/verify-email?token={token}&email={email}"
        
        subject = "Verify your email address"
        body = f"Please click the following link to verify your email address:\n{verification_link}\n\nThis link will expire in {cls.EXPIRY_HOURS} hours."
        
        success = notification_service.send_email(to=email, subject=subject, body=body)
        
        # Log sending status
        IdentityAuditLog.objects.create(
            user=user,
            action=IdentityAuditLog.Action.EMAIL_SENT,
            status="success" if success else "failed",
            metadata={"email": email, "purpose": purpose}
        )
        
        return success
        
    @classmethod
    def verify_token(cls, email: str, purpose: str, token: str, user=None) -> bool:
        """Verify an email token."""
        verification = EmailVerification.objects.filter(
            email=email,
            purpose=purpose,
            is_active=True
        ).order_by("-created_at").first()
        
        if not verification:
            return False
            
        if timezone.now() > verification.expires_at:
            verification.is_active = False
            verification.save(update_fields=["is_active"])
            IdentityAuditLog.objects.create(
                user=user,
                action=IdentityAuditLog.Action.OTP_EXPIRED,
                metadata={"email": email, "purpose": purpose, "reason": "expired"}
            )
            return False
            
        if check_password(token, verification.token_hash):
            verification.verified_at = timezone.now()
            verification.is_active = False # Invalidate to prevent replay
            verification.save(update_fields=["verified_at", "is_active"])
            
            IdentityAuditLog.objects.create(
                user=user,
                action=IdentityAuditLog.Action.EMAIL_VERIFIED,
                metadata={"email": email, "purpose": purpose}
            )
            return True
            
        IdentityAuditLog.objects.create(
            user=user,
            action=IdentityAuditLog.Action.OTP_FAILED,
            status="invalid_token",
            metadata={"email": email, "purpose": purpose}
        )
        return False
