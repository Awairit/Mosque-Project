import io
import sys
from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import OTPVerification
from apps.common.services.otp import OTPService
from apps.common.services.otp_providers import (
    DevelopmentOTPProvider,
    OTPErrorCode,
    TwilioVerifyProvider,
    get_otp_provider,
)


class OTPProviderUnitTests(TestCase):
    def setUp(self):
        self.mobile = "+919011956596"
        self.purpose = "registration"

    @override_settings(OTP_PROVIDER="development")
    def test_development_otp_generation(self):
        """1. Test Development OTP generation and console output."""
        captured_output = io.StringIO()
        sys.stdout = captured_output

        try:
            result = OTPService.generate_and_send_otp(
                mobile_number=self.mobile,
                purpose=self.purpose
            )
        finally:
            sys.stdout = sys.__stdout__

        self.assertTrue(result.success)
        self.assertEqual(result.provider, "development")

        # Verify DB record created
        record = OTPVerification.objects.filter(
            mobile_number=self.mobile,
            purpose=self.purpose,
            is_active=True
        ).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.attempts, 0)
        self.assertEqual(record.max_attempts, 3)

        # Verify console log format
        output = captured_output.getvalue()
        self.assertIn("DEVELOPMENT OTP", output)
        self.assertIn(f"Phone   : {self.mobile}", output)
        self.assertIn(f"Purpose : {self.purpose}", output)
        self.assertIn("Expires : 15 minutes", output)

    @override_settings(OTP_PROVIDER="development")
    def test_development_otp_verification_success(self):
        """2. Test Development OTP verification with correct code."""
        # Create OTP record manually or via service
        provider = DevelopmentOTPProvider()
        code = "482731"
        OTPVerification.objects.create(
            mobile_number=self.mobile,
            otp_hash=provider._generate_code() and __import__("django.contrib.auth.hashers").contrib.auth.hashers.make_password(code),
            purpose=self.purpose,
            expires_at=timezone.now() + timedelta(minutes=10),
            max_attempts=3,
        )

        result = OTPService.verify_otp(
            mobile_number=self.mobile,
            purpose=self.purpose,
            otp=code
        )
        self.assertTrue(result.success)
        self.assertEqual(result.code, OTPErrorCode.SUCCESS)

        # Record should now be inactive and verified
        record = OTPVerification.objects.get(mobile_number=self.mobile, purpose=self.purpose)
        self.assertFalse(record.is_active)
        self.assertIsNotNone(record.verified_at)

    @override_settings(OTP_PROVIDER="development")
    def test_wrong_otp_rejection(self):
        """3. Test Wrong OTP rejection."""
        provider = DevelopmentOTPProvider()
        correct_code = "482731"
        OTPVerification.objects.create(
            mobile_number=self.mobile,
            otp_hash=__import__("django.contrib.auth.hashers").contrib.auth.hashers.make_password(correct_code),
            purpose=self.purpose,
            expires_at=timezone.now() + timedelta(minutes=10),
            max_attempts=3,
        )

        result = OTPService.verify_otp(
            mobile_number=self.mobile,
            purpose=self.purpose,
            otp="000000"
        )
        self.assertFalse(result.success)
        self.assertEqual(result.code, OTPErrorCode.VERIFICATION_FAILED)

        # Verify attempt counter incremented
        record = OTPVerification.objects.get(mobile_number=self.mobile, purpose=self.purpose)
        self.assertEqual(record.attempts, 1)
        self.assertTrue(record.is_active)

    @override_settings(OTP_PROVIDER="development")
    def test_expired_otp_rejection(self):
        """4. Test Expired OTP rejection."""
        code = "123456"
        OTPVerification.objects.create(
            mobile_number=self.mobile,
            otp_hash=__import__("django.contrib.auth.hashers").contrib.auth.hashers.make_password(code),
            purpose=self.purpose,
            expires_at=timezone.now() - timedelta(seconds=10),
            max_attempts=3,
        )

        result = OTPService.verify_otp(
            mobile_number=self.mobile,
            purpose=self.purpose,
            otp=code
        )
        self.assertFalse(result.success)
        self.assertEqual(result.code, OTPErrorCode.OTP_EXPIRED)

        record = OTPVerification.objects.get(mobile_number=self.mobile, purpose=self.purpose)
        self.assertFalse(record.is_active)

    @override_settings(OTP_PROVIDER="development")
    def test_max_attempts_rejection(self):
        """5. Test Maximum-attempt rejection."""
        code = "123456"
        record = OTPVerification.objects.create(
            mobile_number=self.mobile,
            otp_hash=__import__("django.contrib.auth.hashers").contrib.auth.hashers.make_password(code),
            purpose=self.purpose,
            expires_at=timezone.now() + timedelta(minutes=10),
            attempts=3,
            max_attempts=3,
        )

        result = OTPService.verify_otp(
            mobile_number=self.mobile,
            purpose=self.purpose,
            otp=code
        )
        self.assertFalse(result.success)
        self.assertEqual(result.code, OTPErrorCode.VERIFICATION_FAILED)
        self.assertIn("Maximum attempts reached", result.message)

        record.refresh_from_db()
        self.assertFalse(record.is_active)

    @override_settings(OTP_PROVIDER="development")
    def test_purpose_mismatch_rejection(self):
        """6. Test Purpose mismatch rejection."""
        code = "123456"
        OTPVerification.objects.create(
            mobile_number=self.mobile,
            otp_hash=__import__("django.contrib.auth.hashers").contrib.auth.hashers.make_password(code),
            purpose="registration",
            expires_at=timezone.now() + timedelta(minutes=10),
            max_attempts=3,
        )

        # Attempt to verify with purpose 'forgot_password'
        result = OTPService.verify_otp(
            mobile_number=self.mobile,
            purpose="forgot_password",
            otp=code
        )
        self.assertFalse(result.success)
        self.assertEqual(result.code, OTPErrorCode.VERIFICATION_FAILED)

    @override_settings(OTP_PROVIDER="development")
    @patch("apps.common.services.otp_providers.TwilioVerifyProvider.generate_and_send")
    def test_development_provider_does_not_call_twilio(self, mock_twilio_send):
        """7. Test Development provider does not call Twilio."""
        result = OTPService.generate_and_send_otp(
            mobile_number=self.mobile,
            purpose=self.purpose
        )
        self.assertTrue(result.success)
        mock_twilio_send.assert_not_called()

    @override_settings(OTP_PROVIDER="twilio")
    def test_production_config_selects_twilio_provider(self):
        """8. Test Production configuration selects TwilioVerifyProvider."""
        provider = get_otp_provider()
        self.assertIsInstance(provider, TwilioVerifyProvider)


class RegistrationOTPFlowAPITests(APITestCase):
    @override_settings(OTP_PROVIDER="development")
    @patch("apps.common.services.otp_providers.DevelopmentOTPProvider._generate_code", return_value="482731")
    def test_existing_registration_otp_flow(self, mock_gen_code):
        """9. Test full registration OTP request and verification flow end-to-end."""
        mobile = "+919011956596"
        request_url = reverse("registration-otp-request")
        verify_url = reverse("registration-otp-verify")

        # Step 1: Request OTP
        req_res = self.client.post(request_url, {"mobile_number": mobile})
        self.assertEqual(req_res.status_code, status.HTTP_200_OK)
        self.assertEqual(req_res.data["detail"], "OTP sent to your WhatsApp number.")

        # Extract generated OTP from DB
        record = OTPVerification.objects.filter(mobile_number=mobile, purpose="registration", is_active=True).first()
        self.assertIsNotNone(record)
        self.assertTrue(check_password("482731", record.otp_hash))

        # Step 2: Verify OTP
        verify_res = self.client.post(verify_url, {"mobile_number": mobile, "otp": "482731"})
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertIn("verification_token", verify_res.data)
