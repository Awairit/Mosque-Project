from unittest.mock import patch
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from django.utils import timezone

from apps.locations.models import City
from apps.accounts.models import CityAdmin, MosqueAdmin, IdentityAuditLog
from apps.mosques.models import Mosque, MosqueAnnouncement
from apps.prayers.models import PrayerTiming
from apps.common.services.otp_providers import ProviderResult


class MosqueComV2RegressionTests(APITestCase):
    def setUp(self):
        # Create Super Admin User
        self.superadmin_user = User.objects.create_superuser(
            username="superadmin",
            password="superpassword123",
            email="superadmin@example.com",
            last_login=timezone.now()
        )
        self.superadmin_token = Token.objects.create(user=self.superadmin_user)

        # Create Cities
        self.city_mumbai, _ = City.objects.get_or_create(name="Mumbai", defaults={"latitude": 19.0760, "longitude": 72.8777})
        self.city_pune, _ = City.objects.get_or_create(name="Pune", defaults={"latitude": 18.5204, "longitude": 73.8567})

        # Create City Admins
        self.city_admin_user = User.objects.create_user(username="mumbaiadmin", password="password123")
        self.city_admin = CityAdmin.objects.create(
            user=self.city_admin_user,
            city=self.city_mumbai,
            mobile_number="+919876543210"
        )

        self.pune_admin_user = User.objects.create_user(username="puneadmin", password="password123")
        self.pune_admin = CityAdmin.objects.create(
            user=self.pune_admin_user,
            city=self.city_pune,
            mobile_number="+918888888888"
        )

        # Create Active Mosque and MosqueAdmin
        self.mosque_active = Mosque.objects.create(
            mosque_name="Active Central Mosque",
            city="Mumbai",
            city_relation=self.city_mumbai,
            latitude=19.0760,
            longitude=72.8777,
            mosque_status=Mosque.MosqueStatus.ACTIVE
        )
        self.mosque_admin_user = User.objects.create_user(username="activeadmin", password="password123")
        self.mosque_admin = MosqueAdmin.objects.create(
            user=self.mosque_admin_user,
            mosque=self.mosque_active,
            mobile_number="+917777777777"
        )

    def test_super_admin_mosque_lifecycle_status(self):
        # Authenticate as Super Admin
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.superadmin_token.key}")
        url = reverse("platform-admin-mosques-status", kwargs={"pk": self.mosque_active.id})

        # Archive mosque
        response = self.client.patch(url, {"mosque_status": "archived"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.mosque_active.refresh_from_db()
        self.assertEqual(self.mosque_active.mosque_status, "archived")

        # Deactivated mosque admin user
        self.mosque_admin_user.refresh_from_db()
        self.assertFalse(self.mosque_admin_user.is_active)

    def test_login_blocked_if_mosque_inactive_or_archived(self):
        # Archive mosque
        self.mosque_active.mosque_status = Mosque.MosqueStatus.ARCHIVED
        self.mosque_active.save()

        # Login attempt
        url = reverse("auth-login")
        response = self.client.post(url, {
            "mobile_number": "+917777777777",
            "password": "password123"
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("disabled", str(response.data))

    def test_safe_permanent_deletion_validation(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.superadmin_token.key}")
        url = reverse("platform-admin-mosques-delete", kwargs={"pk": self.mosque_active.id})

        # Attach prayer timing to mosque
        PrayerTiming.objects.create(
            mosque=self.mosque_active,
            fajr_time="05:00:00",
            dhuhr_time="12:30:00",
            asr_time="16:00:00",
            maghrib_time="18:30:00",
            isha_time="20:00:00",
            jumuah_time="13:00:00",
            effective_from=timezone.now().date()
        )

        # Deletion attempt should be rejected with 400
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assigned admins", response.data["detail"])

    def test_city_admin_profile_restricted_fields(self):
        self.client.force_authenticate(user=self.city_admin_user)
        url = reverse("city-admin-profile")

        # Try to modify restricted city field
        response = self.client.patch(url, {"city": self.city_pune.id})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Update first_name and email
        response = self.client.patch(url, {"first_name": "NewFirst", "email": "new@example.com"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.city_admin_user.refresh_from_db()
        self.assertEqual(self.city_admin_user.first_name, "NewFirst")
        self.assertEqual(self.city_admin_user.email, "new@example.com")

    def test_city_admin_change_password(self):
        self.client.force_authenticate(user=self.city_admin_user)
        url = reverse("city-admin-change-password")

        response = self.client.post(url, {
            "current_password": "password123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

        # Verify old credentials fail and new password works
        self.client.logout()
        login_url = reverse("auth-login")
        fail_res = self.client.post(login_url, {"mobile_number": "+919876543210", "password": "password123"})
        self.assertEqual(fail_res.status_code, status.HTTP_400_BAD_REQUEST)

        success_res = self.client.post(login_url, {"mobile_number": "+919876543210", "password": "newpassword123"})
        self.assertEqual(success_res.status_code, status.HTTP_200_OK)

    @patch("apps.common.services.otp.OTPService.generate_and_send_otp")
    @patch("apps.common.services.otp.OTPService.verify_otp")
    def test_super_admin_lost_phone_recovery_flow(self, mock_verify, mock_gen):
        mock_gen.return_value = ProviderResult(success=True, code="SUCCESS", message="OTP Sent")
        mock_verify.return_value = ProviderResult(success=True, code="SUCCESS", message="OTP Verified")

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.superadmin_token.key}")
        request_url = reverse("platform-admin-city-admins-change-mobile", kwargs={"pk": self.city_admin.id})
        verify_url = reverse("platform-admin-city-admins-verify-mobile", kwargs={"pk": self.city_admin.id})

        # Initiate recovery
        req_res = self.client.post(request_url, {
            "new_mobile_number": "+919999900000",
            "reason": "Lost SIM card and device"
        })
        self.assertEqual(req_res.status_code, status.HTTP_200_OK)

        # Verify recovery OTP
        ver_res = self.client.post(verify_url, {
            "new_mobile_number": "+919999900000",
            "otp_code": "123456"
        })
        self.assertEqual(ver_res.status_code, status.HTTP_200_OK)
        self.city_admin.refresh_from_db()
        self.assertEqual(self.city_admin.mobile_number, "+919999900000")
