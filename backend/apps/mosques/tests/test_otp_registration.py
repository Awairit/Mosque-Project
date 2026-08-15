from unittest.mock import patch
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.locations.models import City
from apps.mosques.models import MosqueRegistrationRequest
from apps.common.services.otp_providers import DevelopmentOTPProvider


class MosqueRegistrationOTPFlowTests(TestCase):
    """Regression tests for Issue 2: OTP request -> OTP verify -> Registration submission flow."""

    def setUp(self):
        self.client = APIClient()
        self.city = City.objects.create(
            name="Hyderabad",
            latitude=17.3850,
            longitude=78.4867,
            timezone="Asia/Kolkata",
        )
        self.mobile = "+919876543210"

    @patch.object(DevelopmentOTPProvider, "_generate_code", return_value="123456")
    def test_full_otp_registration_flow_succeeds(self, mock_code):
        """1. Request OTP -> 2. Verify OTP -> 3. Submit registration -> 4. Registration succeeds."""
        # 1. Request OTP
        req_res = self.client.post(
            "/api/v1/mosque-registration/otp/request/",
            {"mobile_number": self.mobile},
            format="json",
        )
        self.assertEqual(req_res.status_code, status.HTTP_200_OK)

        # 2. Verify OTP with generated code
        verify_res = self.client.post(
            "/api/v1/mosque-registration/otp/verify/",
            {"mobile_number": self.mobile, "otp": "123456"},
            format="json",
        )
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)
        self.assertIn("verification_token", verify_res.data)
        token = verify_res.data["verification_token"]

        # 3. Verify OTP code cannot be reused on /otp/verify/
        reverify_res = self.client.post(
            "/api/v1/mosque-registration/otp/verify/",
            {"mobile_number": self.mobile, "otp": "123456"},
            format="json",
        )
        self.assertEqual(reverify_res.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. Submit registration using signed verification_token
        reg_res = self.client.post(
            "/api/v1/mosque-registration/",
            {
                "mosque_name": "Masjid An-Noor",
                "admin_name": "Testing Admin",
                "mobile_number": self.mobile,
                "city": "Hyderabad",
                "address": "Street 10, Banjara Hills",
                "verification_token": token,
            },
            format="json",
        )
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            MosqueRegistrationRequest.objects.filter(
                mobile_number=self.mobile, mosque_name="Masjid An-Noor"
            ).exists()
        )
