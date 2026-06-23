from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.accounts.models import MosqueAdmin
from apps.mosques.admin import MosqueRegistrationRequestAdmin
from apps.mosques.models import Mosque, MosqueRegistrationRequest


class MosqueApprovalTests(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = MosqueRegistrationRequestAdmin(
            MosqueRegistrationRequest, self.site
        )

        # Pre-create a request to approve
        self.request_data = MosqueRegistrationRequest.objects.create(
            mosque_name="Al-Noor Mosque",
            admin_name="Ahmad",
            mobile_number="1234567890",
            city="New York",
            address="123 Main St",
            women_prayer_available=True,
            status=MosqueRegistrationRequest.Status.PENDING,
        )

    def test_approval_workflow_creates_user_and_admin(self):
        # Approve the request
        queryset = MosqueRegistrationRequest.objects.filter(
            id=self.request_data.id
        )
        self.admin.approve_selected_requests(None, queryset)

        # Check that mosque is created
        mosque = Mosque.objects.filter(
            mosque_name="Al-Noor Mosque", city="New York"
        ).first()
        self.assertIsNotNone(mosque)

        # Check that user is created
        user = User.objects.filter(
            username=self.request_data.mobile_number
        ).first()
        self.assertIsNotNone(user)

        # Check that MosqueAdmin is created and linked correctly
        mosque_admin = MosqueAdmin.objects.filter(
            mobile_number=self.request_data.mobile_number
        ).first()
        self.assertIsNotNone(mosque_admin)
        self.assertEqual(mosque_admin.user, user)
        self.assertEqual(mosque_admin.mosque, mosque)
        self.assertTrue(mosque_admin.is_active)

    def test_approval_workflow_is_idempotent(self):
        queryset = MosqueRegistrationRequest.objects.filter(
            id=self.request_data.id
        )

        # Approve once
        self.admin.approve_selected_requests(None, queryset)
        mosques_count_first = Mosque.objects.count()
        users_count_first = User.objects.count()
        admins_count_first = MosqueAdmin.objects.count()

        # Approve again
        self.admin.approve_selected_requests(None, queryset)

        self.assertEqual(Mosque.objects.count(), mosques_count_first)
        self.assertEqual(User.objects.count(), users_count_first)
        self.assertEqual(MosqueAdmin.objects.count(), admins_count_first)


class LoginAPITests(APITestCase):
    def setUp(self):
        # Create a mosque and admin user
        self.mosque = Mosque.objects.create(
            mosque_name="Al-Noor Mosque",
            city="New York",
            address="123 Main St",
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        self.user = User.objects.create_user(
            username="1234567890", password="securepassword123"
        )
        self.mosque_admin = MosqueAdmin.objects.create(
            user=self.user,
            mosque=self.mosque,
            mobile_number="1234567890",
            is_active=True,
        )

        self.login_url = reverse("auth-login")

    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {"mobile_number": "1234567890", "password": "securepassword123"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["mobile_number"], "1234567890")
        self.assertEqual(response.data["mosque_id"], self.mosque.id)
        self.assertEqual(
            response.data["mosque_name"], self.mosque.mosque_name
        )

        # Verify token in DB
        token = Token.objects.filter(key=response.data["token"]).first()
        self.assertIsNotNone(token)
        self.assertEqual(token.user, self.user)

    def test_login_failure_invalid_credentials(self):
        # Invalid password
        response = self.client.post(
            self.login_url,
            {"mobile_number": "1234567890", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

        # Invalid mobile number
        response = self.client.post(
            self.login_url,
            {"mobile_number": "9999999999", "password": "securepassword123"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_login_failure_deactivated_admin(self):
        self.mosque_admin.is_active = False
        self.mosque_admin.save()

        response = self.client.post(
            self.login_url,
            {"mobile_number": "1234567890", "password": "securepassword123"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["non_field_errors"],
            ["This account has been disabled."],
        )
