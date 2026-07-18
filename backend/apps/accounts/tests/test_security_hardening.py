from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import CityAdmin, MosqueAdmin, OTPVerification
from apps.locations.models import City
from apps.mosques.models import Mosque, MosqueAnnouncement, MosqueEvent
from apps.common.storage import SafeCloudinaryStorage


class DisableThrottlingTestCase(TestCase):
    """Base test case that disables Django REST Framework view rate limits during tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from apps.accounts.views import (
            ForgotPasswordRequestAPIView,
            ForgotPasswordVerifyAPIView,
            ForgotPasswordResetAPIView,
        )
        cls._original_throttles = {
            ForgotPasswordRequestAPIView: ForgotPasswordRequestAPIView.throttle_classes,
            ForgotPasswordVerifyAPIView: ForgotPasswordVerifyAPIView.throttle_classes,
            ForgotPasswordResetAPIView: ForgotPasswordResetAPIView.throttle_classes,
        }
        ForgotPasswordRequestAPIView.throttle_classes = []
        ForgotPasswordVerifyAPIView.throttle_classes = []
        ForgotPasswordResetAPIView.throttle_classes = []

    @classmethod
    def tearDownClass(cls):
        for view_class, throttles in cls._original_throttles.items():
            view_class.throttle_classes = throttles
        super().tearDownClass()


class CloudStorageHardeningTests(TestCase):
    """Automated tests for SafeCloudinaryStorage security hardening."""

    @override_settings(
        CLOUDINARY_STORAGE={
            "CLOUD_NAME": "test_cloud",
            "API_KEY": "test_key",
            "API_SECRET": "test_secret",
        }
    )
    def test_storage_init_success(self):
        """Storage initializes successfully when valid settings are provided."""
        storage = SafeCloudinaryStorage()
        self.assertIsNotNone(storage)

    @patch("apps.common.storage.settings")
    def test_storage_init_missing_credentials(self, mock_settings):
        """Storage initialization raises ImproperlyConfigured if credentials are empty."""
        mock_settings.CLOUDINARY_STORAGE = {}
        with self.assertRaises(ImproperlyConfigured):
            SafeCloudinaryStorage()

    @patch("apps.common.storage.settings")
    def test_storage_init_invalid_configuration(self, mock_settings):
        """Storage initialization raises ImproperlyConfigured if invalid configuration is detected."""
        mock_settings.CLOUDINARY_STORAGE = {
            "CLOUD_NAME": "INVALID_NAME",
            "API_KEY": "test_key",
            "API_SECRET": "test_secret",
        }
        with self.assertRaises(ImproperlyConfigured):
            SafeCloudinaryStorage()

    @override_settings(
        CLOUDINARY_STORAGE={
            "CLOUD_NAME": "test_cloud",
            "API_KEY": "test_key",
            "API_SECRET": "test_secret",
        }
    )
    @patch("cloudinary_storage.storage.MediaCloudinaryStorage._save")
    def test_storage_save_success(self, mock_save):
        """Successful upload delegates to the parent class save logic."""
        mock_save.return_value = "media/test_image.jpg"
        storage = SafeCloudinaryStorage()
        res = storage._save("test_image.jpg", None)
        self.assertEqual(res, "media/test_image.jpg")

    @override_settings(
        CLOUDINARY_STORAGE={
            "CLOUD_NAME": "test_cloud",
            "API_KEY": "test_key",
            "API_SECRET": "test_secret",
        }
    )
    @patch("cloudinary_storage.storage.MediaCloudinaryStorage._save")
    def test_storage_save_failure(self, mock_save):
        """Gracefully handles upload failures by converting them into clean IOErrors."""
        mock_save.side_effect = Exception("Cloudinary connection reset")
        storage = SafeCloudinaryStorage()
        with self.assertRaises(IOError):
            storage._save("test_image.jpg", None)


class NotificationAuthorizationTests(TestCase):
    """Automated tests for City Admin notification and resource authorization constraints."""

    def setUp(self):
        self.client = APIClient()

        # Create cities
        self.city_a, _ = City.objects.get_or_create(name="Notification City A", defaults={"latitude": 12.0, "longitude": 77.0})
        self.city_b, _ = City.objects.get_or_create(name="Notification City B", defaults={"latitude": 13.0, "longitude": 78.0})

        # Create City Admin A
        self.user_city_admin_a = User.objects.create_user(
            username="city_admin_a", password="password123", email="admina@city.com"
        )
        self.city_admin_a = CityAdmin.objects.create(
            user=self.user_city_admin_a,
            city=self.city_a,
            mobile_number="+919999999991",
            is_active=True,
        )
        from rest_framework.authtoken.models import Token
        self.token_city_admin_a, _ = Token.objects.get_or_create(
            user=self.user_city_admin_a
        )

        # Create City Admin B
        self.user_city_admin_b = User.objects.create_user(
            username="city_admin_b", password="password123", email="adminb@city.com"
        )
        self.city_admin_b = CityAdmin.objects.create(
            user=self.user_city_admin_b,
            city=self.city_b,
            mobile_number="+919999999992",
            is_active=True,
        )
        self.token_city_admin_b, _ = Token.objects.get_or_create(
            user=self.user_city_admin_b
        )

        # Create Mosques
        self.mosque_a = Mosque.objects.create(
            mosque_name="Mosque A", city="City A", city_relation=self.city_a
        )
        self.mosque_b = Mosque.objects.create(
            mosque_name="Mosque B", city="City B", city_relation=self.city_b
        )

        # Create Mosque Admin A
        self.user_mosque_admin_a = User.objects.create_user(
            username="mosque_admin_a", password="password123", email="admina@mosque.com"
        )
        self.mosque_admin_a = MosqueAdmin.objects.create(
            user=self.user_mosque_admin_a,
            mosque=self.mosque_a,
            mobile_number="+918888888881",
            is_active=True,
        )

        # Create Mosque Admin B
        self.user_mosque_admin_b = User.objects.create_user(
            username="mosque_admin_b", password="password123", email="adminb@mosque.com"
        )
        self.mosque_admin_b = MosqueAdmin.objects.create(
            user=self.user_mosque_admin_b,
            mosque=self.mosque_b,
            mobile_number="+918888888882",
            is_active=True,
        )

    # ── Notification Send Tests ──────────────────────────────────────

    @patch("apps.common.services.notification.notification_service.send_sms")
    def test_valid_city_admin_sends_notification(self, mock_send_sms):
        """City Admin A can successfully send a notification to a Mosque Admin in City A."""
        mock_send_sms.return_value = True
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_city_admin_a.key}")

        url = reverse("city-admin-notifications-send")
        data = {
            "channel": "sms",
            "recipient": self.mosque_admin_a.mobile_number,
            "message": "Assalamu Alaikum Mosque Admin A",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_cross_city_notification_attempt_fails(self):
        """City Admin A is blocked (403 Forbidden) from sending notifications to Mosque Admin in City B."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_city_admin_a.key}")

        url = reverse("city-admin-notifications-send")
        data = {
            "channel": "sms",
            "recipient": self.mosque_admin_b.mobile_number,
            "message": "Cross city message spam",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("not authorized", str(response.data["detail"]))

    def test_arbitrary_recipient_notification_attempt_fails(self):
        """City Admin A is blocked from sending notifications to unregistered or arbitrary recipients."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_city_admin_a.key}")

        url = reverse("city-admin-notifications-send")
        data = {
            "channel": "sms",
            "recipient": "+917777777777",  # unregistered arbitrary number
            "message": "Arbitrary message",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthorized_request_fails(self):
        """An unauthenticated request to the notification dispatch view is rejected."""
        url = reverse("city-admin-notifications-send")
        data = {
            "channel": "sms",
            "recipient": self.mosque_admin_a.mobile_number,
            "message": "Anonymous message",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ── Resource Allocation (Events & Announcements) Tests ───────────

    def test_cross_city_announcement_update_fails(self):
        """City Admin A is blocked from updating an announcement to point to a Mosque in City B."""
        announcement = MosqueAnnouncement.objects.create(
            mosque=self.mosque_a,
            city=self.city_a,
            title="City A Announcement",
            content="Content",
            status="published",
            is_active=True,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=1),
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_city_admin_a.key}")
        url = reverse("city-admin-announcements-detail", kwargs={"pk": announcement.pk})
        # Attempt to link the announcement to Mosque B (which is in City B)
        data = {"mosque": self.mosque_b.id}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("only assign announcements to mosques in your city", str(response.data))

    def test_cross_city_event_update_fails(self):
        """City Admin A is blocked from updating an event to point to a Mosque in City B."""
        event = MosqueEvent.objects.create(
            mosque=self.mosque_a,
            city=self.city_a,
            title="City A Event",
            description="Description",
            event_date=timezone.now().date(),
            event_time="18:00:00",
            status="published",
            is_active=True,
        )

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token_city_admin_a.key}")
        url = reverse("city-admin-events-detail", kwargs={"pk": event.pk})
        # Attempt to link the event to Mosque B
        data = {"mosque": self.mosque_b.id}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("only assign events to mosques in your city", str(response.data))


class PasswordResetTokenHardeningTests(DisableThrottlingTestCase):
    """Automated tests for password reset token security and single-use constraints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="mosque_admin_user", password="oldpassword123", email="user@mosque.com"
        )
        self.mosque = Mosque.objects.create(mosque_name="Test Mosque", city="Pune Security Hardening")
        self.mosque_admin = MosqueAdmin.objects.create(
            user=self.user,
            mosque=self.mosque,
            mobile_number="+918888888888",
            is_active=True,
        )

    def _get_verified_reset_token(self):
        """Helper to generate a valid signed reset token by verifying an OTP."""
        # Create OTP record
        otp_hash = "hashed_otp_code"
        OTPVerification.objects.create(
            mobile_number=self.mosque_admin.mobile_number,
            otp_hash=otp_hash,
            purpose="forgot_password",
            expires_at=timezone.now() + timedelta(minutes=5),
            is_active=True,
        )
        # Verify OTP using the view to obtain the signed token
        with patch("apps.common.services.otp.OTPService.verify_otp") as mock_verify:
            from apps.common.services.otp_providers import ProviderResult
            mock_verify.return_value = ProviderResult(success=True, code="SUCCESS", message="Success")
            
            url = reverse("auth-forgot-password-verify")
            data = {"mobile_number": self.mosque_admin.mobile_number, "otp": "123456"}
            response = self.client.post(url, data)
            return response.data["reset_token"]

    def test_successful_password_reset(self):
        """User can successfully reset their password with a fresh token."""
        token = self._get_verified_reset_token()
        url = reverse("auth-forgot-password-reset")
        data = {"reset_token": token, "new_password": "newpassword123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

    def test_token_reuse_fails_immediately(self):
        """Token becomes invalid immediately after successful use and cannot be reused."""
        token = self._get_verified_reset_token()
        url = reverse("auth-forgot-password-reset")
        data = {"reset_token": token, "new_password": "newpassword123"}
        
        # First reset succeeds
        response1 = self.client.post(url, data)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        # Second reset with identical token fails
        data["new_password"] = "anotherpassword123"
        response2 = self.client.post(url, data)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been used", str(response2.data["non_field_errors"]))

    def test_invalid_reset_token_fails(self):
        """Verifying with a malformed or corrupted token fails validation."""
        url = reverse("auth-forgot-password-reset")
        data = {"reset_token": "corrupted_or_invalid_token", "new_password": "newpassword123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or expired reset token", str(response.data["non_field_errors"]))

    @patch("django.core.signing.TimestampSigner.unsign")
    def test_expired_reset_token_fails(self, mock_unsign):
        """Expired reset tokens are rejected by the unsign validator."""
        from django.core.signing import SignatureExpired
        mock_unsign.side_effect = SignatureExpired("Signature expired")

        url = reverse("auth-forgot-password-reset")
        data = {"reset_token": "expired_token", "new_password": "newpassword123"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid or expired reset token", str(response.data["non_field_errors"]))


class CityAdminPasswordRecoveryTests(DisableThrottlingTestCase):
    """Automated tests for City Admin forgotten password recovery workflows."""

    def setUp(self):
        self.client = APIClient()

        # Create City Admin profile
        self.user_city = User.objects.create_user(
            username="city_admin_user", password="oldpassword123", email="city@admin.com"
        )
        self.city, _ = City.objects.get_or_create(
            name="Pune Security Hardening",
            defaults={"latitude": 18.5204, "longitude": 73.8567}
        )
        self.city_admin = CityAdmin.objects.create(
            user=self.user_city,
            city=self.city,
            mobile_number="+919999999999",
            is_active=True,
        )

        # Create Mosque Admin profile
        self.user_mosque = User.objects.create_user(
            username="mosque_admin_user", password="oldpassword123", email="mosque@admin.com"
        )
        self.mosque = Mosque.objects.create(mosque_name="Pune Mosque", city="Pune Security Hardening")
        self.mosque_admin = MosqueAdmin.objects.create(
            user=self.user_mosque,
            mosque=self.mosque,
            mobile_number="+918888888888",
            is_active=True,
        )

    @patch("apps.common.services.otp.OTPService.generate_and_send_otp")
    def test_city_admin_forgot_password_request_success(self, mock_otp):
        """City Admin profile matches and successfully triggers OTP dispatch."""
        from apps.common.services.otp_providers import ProviderResult
        mock_otp.return_value = ProviderResult(success=True, code="SUCCESS", message="Success")

        url = reverse("auth-forgot-password-request")
        data = {"mobile_number": self.city_admin.mobile_number}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify success message and OTP trigger
        self.assertIn("If the number exists", response.data["detail"])
        mock_otp.assert_called_once_with(
            mobile_number=self.city_admin.mobile_number,
            purpose="forgot_password",
            user=self.user_city,
        )

    def test_forgot_password_request_invalid_phone(self):
        """An unregistered number triggers a mock 200 response to prevent account enumeration."""
        url = reverse("auth-forgot-password-request")
        data = {"mobile_number": "+917777777777"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("If the number exists", response.data["detail"])

    @patch("apps.common.services.otp.OTPService.verify_otp")
    def test_city_admin_recovery_workflow_successful_reset(self, mock_verify):
        """A complete recovery cycle (OTP verify + Reset) works successfully for City Admins."""
        from apps.common.services.otp_providers import ProviderResult
        mock_verify.return_value = ProviderResult(success=True, code="SUCCESS", message="Success")

        # 1. Verify OTP to get signed token
        verify_url = reverse("auth-forgot-password-verify")
        verify_data = {"mobile_number": self.city_admin.mobile_number, "otp": "123456"}
        verify_res = self.client.post(verify_url, verify_data)
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        reset_token = verify_res.data["reset_token"]

        # 2. Reset password
        reset_url = reverse("auth-forgot-password-reset")
        reset_data = {"reset_token": reset_token, "new_password": "newcitypassword123"}
        reset_res = self.client.post(reset_url, reset_data)
        self.assertEqual(reset_res.status_code, status.HTTP_200_OK)

        # Verify password changed
        self.user_city.refresh_from_db()
        self.assertTrue(self.user_city.check_password("newcitypassword123"))

    @patch("apps.common.services.otp.OTPService.generate_and_send_otp")
    def test_mosque_admin_recovery_flow_unaffected(self, mock_otp):
        """Mosque Admin password recovery flows continue to function exactly as before."""
        from apps.common.services.otp_providers import ProviderResult
        mock_otp.return_value = ProviderResult(success=True, code="SUCCESS", message="Success")

        url = reverse("auth-forgot-password-request")
        data = {"mobile_number": self.mosque_admin.mobile_number}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_otp.assert_called_once_with(
            mobile_number=self.mosque_admin.mobile_number,
            purpose="forgot_password",
            user=self.user_mosque,
        )
