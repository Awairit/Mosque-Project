from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.locations.models import City
from apps.mosques.models import Mosque, MosqueRegistrationRequest
from apps.accounts.models import MosqueAdmin
from apps.platform_admin.models import MosqueApprovalLog


class SuperAdminRequestsWorkflowTests(APITestCase):
    def setUp(self):
        # Create superuser
        self.super_user = User.objects.create_superuser(
            username="superadmin",
            password="superpassword",
            email="super@mosquefinder.org"
        )
        # Create normal user
        self.normal_user = User.objects.create_user(
            username="normaluser",
            password="normalpassword"
        )
        # Create test requests
        self.pending_req = MosqueRegistrationRequest.objects.create(
            mosque_name="Pending Masjid Al-Aqsa",
            admin_name="Omar",
            mobile_number="+919999999999",
            city="Mumbai",
            address="Mohammed Ali Road",
            google_maps_link="https://maps.google.com/?q=mumbai",
            women_prayer_available=True,
            notes="Requires fast approval",
            status=MosqueRegistrationRequest.Status.PENDING
        )

        self.list_url = reverse("platform-admin-requests-list")
        self.detail_url = reverse("platform-admin-requests-detail", args=[self.pending_req.id])
        self.approve_url = reverse("platform-admin-requests-approve", args=[self.pending_req.id])
        self.reject_url = reverse("platform-admin-requests-reject", args=[self.pending_req.id])

    def test_list_requests_unauthorized_denied(self):
        # No authentication
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Non-super user
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_and_search_requests_success(self):
        self.client.force_authenticate(user=self.super_user)

        # Basic list
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["mosque_name"], "Pending Masjid Al-Aqsa")

        # Search matching
        response = self.client.get(f"{self.list_url}?search=Al-Aqsa")
        self.assertEqual(response.data["count"], 1)

        # Search non-matching
        response = self.client.get(f"{self.list_url}?search=Nonexistent")
        self.assertEqual(response.data["count"], 0)

    def test_detail_request_success(self):
        self.client.force_authenticate(user=self.super_user)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["mosque_name"], "Pending Masjid Al-Aqsa")
        self.assertEqual(response.data["notes"], "Requires fast approval")

    def test_approve_request_success(self):
        self.client.force_authenticate(user=self.super_user)
        response = self.client.post(self.approve_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("temp_password", response.data)
        self.assertEqual(response.data["username"], "+919999999999")

        # Check request model fields updated
        self.pending_req.refresh_from_db()
        self.assertEqual(self.pending_req.status, MosqueRegistrationRequest.Status.APPROVED)
        self.assertEqual(self.pending_req.approved_by, self.super_user)
        self.assertIsNotNone(self.pending_req.approved_at)

        # Check Mosque created
        mosque = Mosque.objects.get(mosque_name="Pending Masjid Al-Aqsa")
        self.assertEqual(mosque.city, "Mumbai")
        self.assertEqual(mosque.address, "Mohammed Ali Road")
        self.assertEqual(mosque.google_maps_url, "https://maps.google.com/?q=mumbai")
        self.assertTrue(mosque.women_prayer_available)
        self.assertEqual(mosque.mosque_status, Mosque.MosqueStatus.ACTIVE)

        # Check User created and authenticated using generated password
        user = User.objects.get(username="+919999999999")
        self.assertTrue(user.check_password(response.data["temp_password"]))

        # Check MosqueAdmin created
        mosque_admin = MosqueAdmin.objects.get(user=user)
        self.assertEqual(mosque_admin.mosque, mosque)
        self.assertEqual(mosque_admin.mobile_number, "+919999999999")
        self.assertTrue(mosque_admin.is_active)

        # Check ApprovalLog entry created
        log = MosqueApprovalLog.objects.get(registration_request_id=self.pending_req.id)
        self.assertEqual(log.action, MosqueApprovalLog.ActionTypes.APPROVE)
        self.assertEqual(log.mosque, mosque)
        self.assertEqual(log.admin, self.super_user)

    def test_reject_request_requires_reason(self):
        self.client.force_authenticate(user=self.super_user)
        # Empty reason
        response = self.client.post(self.reject_url, {"reason": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reason", response.data)

        # No reason payload
        response = self.client.post(self.reject_url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reject_request_success(self):
        self.client.force_authenticate(user=self.super_user)
        response = self.client.post(self.reject_url, {"reason": "Duplicate registration request"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check request model fields updated
        self.pending_req.refresh_from_db()
        self.assertEqual(self.pending_req.status, MosqueRegistrationRequest.Status.REJECTED)
        self.assertEqual(self.pending_req.rejected_by, self.super_user)
        self.assertIsNotNone(self.pending_req.rejected_at)
        self.assertEqual(self.pending_req.rejection_reason, "Duplicate registration request")

        # Check NO Mosque created
        self.assertFalse(Mosque.objects.filter(mosque_name="Pending Masjid Al-Aqsa").exists())

        # Check ApprovalLog entry created
        log = MosqueApprovalLog.objects.get(registration_request_id=self.pending_req.id)
        self.assertEqual(log.action, MosqueApprovalLog.ActionTypes.REJECT)
        self.assertIsNone(log.mosque)
        self.assertEqual(log.admin, self.super_user)
        self.assertEqual(log.reason, "Duplicate registration request")

    def test_mark_under_verification_success(self):
        self.client.force_authenticate(user=self.super_user)
        url = reverse("platform-admin-requests-under-verification", args=[self.pending_req.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.pending_req.refresh_from_db()
        self.assertEqual(self.pending_req.status, MosqueRegistrationRequest.Status.UNDER_VERIFICATION)
        self.assertEqual(self.pending_req.under_verification_by, self.super_user)
        self.assertIsNotNone(self.pending_req.under_verification_at)

    def test_save_verification_notes_success(self):
        self.client.force_authenticate(user=self.super_user)
        url = reverse("platform-admin-requests-verification-notes", args=[self.pending_req.id])
        response = self.client.patch(url, {"super_admin_notes": "Verified details via phone call."})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.pending_req.refresh_from_db()
        self.assertEqual(self.pending_req.super_admin_notes, "Verified details via phone call.")
