"""OTP Service for Identity Verification.

OTPService is the single entry-point for all OTP operations.  It is
responsible for:

  - Audit logging (IdentityAuditLog) for every OTP event.
  - Delegating generation/sending and verification to the configured
    OTPProvider.

The OTPProvider is selected via the OTP_PROVIDER environment variable:
  OTP_PROVIDER=dummy   → DummyOTPProvider (local development)
  OTP_PROVIDER=twilio  → TwilioVerifyProvider (production)

Business logic in views/serializers must call only OTPService.  No view
should import from otp_providers directly.
"""

import logging
from typing import Optional

from django.contrib.auth import get_user_model

from apps.accounts.models import IdentityAuditLog
from apps.common.services.otp_providers import get_otp_provider

logger = logging.getLogger(__name__)

User = get_user_model()


class OTPService:
    """Central service for OTP generation and verification.

    All audit logging lives here so it is provider-agnostic.
    """

    @classmethod
    def generate_and_send_otp(
        cls,
        mobile_number: str,
        purpose: str,
        user: Optional[object] = None,
    ) -> bool:
        """Generate an OTP and send it to *mobile_number*.

        Returns True if the OTP was dispatched successfully.
        """
        provider = get_otp_provider()

        # Audit: generation attempt
        IdentityAuditLog.objects.create(
            user=user,
            action=IdentityAuditLog.Action.OTP_GENERATED,
            metadata={"mobile_number": mobile_number, "purpose": purpose},
        )

        success = provider.generate_and_send(mobile_number=mobile_number, purpose=purpose)

        # Audit: send outcome
        IdentityAuditLog.objects.create(
            user=user,
            action=IdentityAuditLog.Action.OTP_SENT,
            status="success" if success else "failed",
            metadata={"mobile_number": mobile_number, "purpose": purpose},
        )

        return success

    @classmethod
    def verify_otp(
        cls,
        mobile_number: str,
        purpose: str,
        otp: str,
        user: Optional[object] = None,
    ) -> bool:
        """Verify an OTP submitted by the user.

        Returns True if the code is valid and the verification succeeded.
        """
        provider = get_otp_provider()

        verified = provider.verify(mobile_number=mobile_number, purpose=purpose, code=otp)

        if verified:
            IdentityAuditLog.objects.create(
                user=user,
                action=IdentityAuditLog.Action.OTP_VERIFIED,
                metadata={"mobile_number": mobile_number, "purpose": purpose},
            )
        else:
            IdentityAuditLog.objects.create(
                user=user,
                action=IdentityAuditLog.Action.OTP_FAILED,
                status="invalid_code",
                metadata={"mobile_number": mobile_number, "purpose": purpose},
            )

        return verified
