"""OTP Provider Abstraction for the Mosque Platform.

This module defines the OTPProvider interface and concrete implementations:
  - DummyOTPProvider: For local development (no external service required).
  - TwilioVerifyProvider: For production via Twilio Verify (no Twilio phone
    number needed — only a Verify Service SID).

To switch providers, set OTP_PROVIDER in your .env:
  OTP_PROVIDER=dummy   → DummyOTPProvider
  OTP_PROVIDER=twilio  → TwilioVerifyProvider

Adding a new provider (MSG91, AWS SNS, etc.) requires only:
  1. Subclassing BaseOTPProvider.
  2. Adding a branch in get_otp_provider().
No business logic changes are needed.
"""

import logging
import random
import string
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone

from apps.accounts.models import IdentityAuditLog, OTPVerification

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract interface
# ---------------------------------------------------------------------------

class BaseOTPProvider(ABC):
    """Interface every OTP provider must implement.

    Providers are responsible only for:
      - Sending an OTP to a mobile number.
      - Verifying a code submitted by the user.

    Audit logging, throttling, and all business rules remain in OTPService.
    """

    @abstractmethod
    def generate_and_send(self, mobile_number: str, purpose: str) -> bool:
        """Generate an OTP and deliver it to *mobile_number*.

        Args:
            mobile_number: E.164-formatted phone number (e.g. +919876543210).
            purpose: Logical label for the OTP (e.g. 'registration', 'password_reset').

        Returns:
            True if the OTP was dispatched successfully, False otherwise.
        """

    @abstractmethod
    def verify(self, mobile_number: str, purpose: str, code: str) -> bool:
        """Verify a code that the user submitted.

        Args:
            mobile_number: The same number used when calling generate_and_send.
            purpose: The same purpose label used when calling generate_and_send.
            code: The code entered by the user.

        Returns:
            True if the code is valid, False otherwise.
        """


# ---------------------------------------------------------------------------
# DummyOTPProvider  (development / testing)
# ---------------------------------------------------------------------------

class DummyOTPProvider(BaseOTPProvider):
    """Local OTP provider that stores codes in the database.

    - No external service is required.
    - Generated OTPs are printed to the Django console so developers can
      complete flows without a real phone.
    - DummyNotificationProvider is used to log the SMS delivery.
    """

    OTP_LENGTH = 6
    EXPIRY_MINUTES = 10
    MAX_ATTEMPTS = 3

    # Import lazily to avoid circular imports at module load time.
    @staticmethod
    def _notification_service():
        from apps.common.services.notification import notification_service
        return notification_service

    def _generate_code(self) -> str:
        return "".join(random.choices(string.digits, k=self.OTP_LENGTH))

    def generate_and_send(self, mobile_number: str, purpose: str) -> bool:
        # Invalidate any existing active OTPs for this number + purpose.
        OTPVerification.objects.filter(
            mobile_number=mobile_number,
            purpose=purpose,
            is_active=True,
        ).update(is_active=False)

        # Dynamic expiry based on purpose
        expiry_minutes = 10
        if purpose == "registration":
            expiry_minutes = 15
        elif purpose == "forgot_password":
            expiry_minutes = 10
        elif purpose == "login":
            expiry_minutes = 5

        code = self._generate_code()
        otp_hash = make_password(code)
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

        OTPVerification.objects.create(
            mobile_number=mobile_number,
            otp_hash=otp_hash,
            purpose=purpose,
            expires_at=expires_at,
            max_attempts=self.MAX_ATTEMPTS,
        )

        message = (
            f"Your verification code is {code}. "
            f"It expires in {expiry_minutes} minutes."
        )
        return self._notification_service().send_sms(
            recipient=mobile_number, message=message
        )

    def verify(self, mobile_number: str, purpose: str, code: str) -> bool:
        verification = (
            OTPVerification.objects.filter(
                mobile_number=mobile_number,
                purpose=purpose,
                is_active=True,
            )
            .order_by("-created_at")
            .first()
        )

        if not verification:
            return False

        if verification.attempts >= verification.max_attempts:
            verification.is_active = False
            verification.save(update_fields=["is_active"])
            return False

        if timezone.now() > verification.expires_at:
            verification.is_active = False
            verification.save(update_fields=["is_active"])
            return False

        verification.attempts += 1

        if check_password(code, verification.otp_hash):
            verification.verified_at = timezone.now()
            verification.is_active = False
            verification.save(update_fields=["attempts", "verified_at", "is_active"])
            return True

        verification.save(update_fields=["attempts"])
        return False


# ---------------------------------------------------------------------------
# TwilioVerifyProvider  (production)
# ---------------------------------------------------------------------------

class TwilioVerifyProvider(BaseOTPProvider):
    """OTP provider backed by Twilio Verify.

    Twilio Verify generates, sends, and validates OTPs on its side.
    No Twilio phone number is required — only the Verify Service SID.

    Credentials are read from Django settings which are sourced from
    environment variables:
      TWILIO_ACCOUNT_SID
      TWILIO_AUTH_TOKEN
      TWILIO_VERIFY_SERVICE_SID
    """

    def __init__(self):
        self._client: Optional[object] = None  # Lazy-initialised Twilio client

    def _get_client(self):
        """Return a cached Twilio REST client, initialised on first call."""
        if self._client is None:
            try:
                from twilio.rest import Client  # type: ignore[import]
            except ImportError as exc:
                raise RuntimeError(
                    "The 'twilio' package is required for TwilioVerifyProvider. "
                    "Install it with: pip install twilio"
                ) from exc

            account_sid = settings.TWILIO_ACCOUNT_SID
            auth_token = settings.TWILIO_AUTH_TOKEN

            if not account_sid or not auth_token:
                raise RuntimeError(
                    "TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in your environment."
                )

            self._client = Client(account_sid, auth_token)

        return self._client

    def _service_sid(self) -> str:
        sid = settings.TWILIO_VERIFY_SERVICE_SID
        if not sid:
            raise RuntimeError(
                "TWILIO_VERIFY_SERVICE_SID must be set in your environment."
            )
        return sid

    def generate_and_send(self, mobile_number: str, purpose: str) -> bool:
        """Trigger Twilio Verify to send an SMS OTP to *mobile_number*."""
        if settings.DEBUG:
            print("\n" + "=" * 60)
            print("🚀 TWILIO VERIFY PROVIDER - DISPATCHING OTP")
            print("=" * 60)
            print(f"Original Phone   : {mobile_number}")
            print(f"Normalized Phone : {mobile_number} (E.164)")
            print(f"Active Provider  : TwilioVerifyProvider")
            print(f"Purpose          : {purpose}")
            print("=" * 60)

        try:
            client = self._get_client()
            verification = (
                client.verify.v2
                .services(self._service_sid())
                .verifications.create(to=mobile_number, channel="sms")
            )
            
            if settings.DEBUG:
                print(f"Twilio Status    : {verification.status}")
                print(f"Verification SID : {verification.sid}")
                print("=" * 60 + "\n")

            logger.info(
                "Twilio Verify OTP sent to %s (status=%s, purpose=%s)",
                mobile_number,
                verification.status,
                purpose,
            )
            return verification.status in ("pending", "approved")
        except Exception as exc:
            if settings.DEBUG:
                print(f"❌ Twilio Exception: {str(exc)}")
                print("=" * 60 + "\n")
            logger.error(
                "Twilio Verify send failed for %s (purpose=%s): %s",
                mobile_number,
                purpose,
                exc,
            )
            if settings.DEBUG:
                raise exc
            return False

    def verify(self, mobile_number: str, purpose: str, code: str) -> bool:
        """Ask Twilio Verify whether *code* is correct for *mobile_number*."""
        if settings.DEBUG:
            print("\n" + "=" * 60)
            print("🚀 TWILIO VERIFY PROVIDER - CHECKING OTP")
            print("=" * 60)
            print(f"Phone Number     : {mobile_number}")
            print(f"Active Provider  : TwilioVerifyProvider")
            print(f"Purpose          : {purpose}")
            print("=" * 60)

        try:
            client = self._get_client()
            check = (
                client.verify.v2
                .services(self._service_sid())
                .verification_checks.create(to=mobile_number, code=code)
            )
            approved = check.status == "approved"
            
            if settings.DEBUG:
                print(f"Twilio Status    : {check.status}")
                print(f"Verification SID : {check.sid}")
                print(f"Result           : {'Approved' if approved else 'Failed'}")
                print("=" * 60 + "\n")

            logger.info(
                "Twilio Verify check for %s (purpose=%s): status=%s",
                mobile_number,
                purpose,
                check.status,
            )
            return approved
        except Exception as exc:
            if settings.DEBUG:
                print(f"❌ Twilio Exception: {str(exc)}")
                print("=" * 60 + "\n")
            logger.error(
                "Twilio Verify check failed for %s (purpose=%s): %s",
                mobile_number,
                purpose,
                exc,
            )
            if settings.DEBUG:
                raise exc
            return False


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_otp_provider() -> BaseOTPProvider:
    """Return the configured OTP provider based on ``settings.OTP_PROVIDER``.

    OTP_PROVIDER=dummy   → DummyOTPProvider
    OTP_PROVIDER=twilio  → TwilioVerifyProvider

    New providers can be added here without touching any business logic.
    """
    provider_name = getattr(settings, "OTP_PROVIDER", "dummy").strip().lower()

    if provider_name == "twilio":
        logger.info("OTP provider: TwilioVerifyProvider")
        return TwilioVerifyProvider()

    if provider_name == "dummy":
        logger.info("OTP provider: DummyOTPProvider")
        return DummyOTPProvider()

    raise ValueError(
        f"Unknown OTP_PROVIDER '{provider_name}'. "
        "Supported values: 'dummy', 'twilio'."
    )
