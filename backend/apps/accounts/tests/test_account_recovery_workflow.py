"""Automated unit tests for Account Recovery submission, Super Admin management, security, and multi-role safety."""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import AccountRecoveryRequest, CityAdmin, MosqueAdmin
from apps.locations.models import City
from apps.mosques.models import Mosque


class AccountRecoveryWorkflowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.city_nanded, _ = City.objects.get_or_create(
            name="Nanded",
            defaults={"latitude": 19.1383, "longitude": 77.3210, "timezone": "Asia/Kolkata"}
        )
        self.mosque_quba, _ = Mosque.objects.get_or_create(
            mosque_name="Masjide Quba",
            defaults={
                "city": "Nanded",
                "city_relation": self.city_nanded,
                "address": "Nanded Town",
                "mosque_status": Mosque.MosqueStatus.ACTIVE,
            }
        )

        # Super Admin user
        self.super_admin = User.objects.create_superuser(
            username="+919999999999",
            password="SuperPassword123!",
            email="superadmin@mosquecom.org"
        )

        # Dual-Role User (Mohammad Irshad: City Admin + Mosque Admin)
        self.user_irshad = User.objects.create_user(
            username="+919011956596",
            password="UserPassword123!",
            first_name="Mohammad",
            last_name="Irshad",
            email="irshad@example.com",
        )
        self.city_admin = CityAdmin.objects.create(
            user=self.user_irshad,
            city=self.city_nanded,
            mobile_number="+919011956596",
            is_active=True,
        )
        self.mosque_admin = MosqueAdmin.objects.create(
            user=self.user_irshad,
            mosque=self.mosque_quba,
            mobile_number="+919011956596",
            is_active=True,
        )

        # Normal User
        self.user_normal = User.objects.create_user(
            username="+919888877777",
            password="UserPassword123!",
            first_name="Normal",
            last_name="User",
        )

        # URLs
        self.public_recovery_url = reverse("auth-account-recovery")
        self.super_admin_list_url = reverse("platform-admin-recovery-list")

    def test_user_can_submit_recovery_request(self):
        """Test 1: Public user can submit recovery request with valid previous contact, persisted with status=pending."""
        payload = {
            "mosque_id": self.mosque_quba.id,
            "mosque_name": "Masjide Quba",
            "applicant_name": "Mohammad Irshad",
            "previous_registered_contact": "+919011956596",
            "contact_email": "irshad@example.com",
            "contact_whatsapp": "+919876543210",
            "notes": "Lost phone number while travelling.",
        }
        res = self.client.post(self.public_recovery_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", res.data)

        # Verify DB Persistence
        req_obj = AccountRecoveryRequest.objects.get(pk=res.data["id"])
        self.assertEqual(req_obj.mosque, self.mosque_quba)
        self.assertEqual(req_obj.mosque_name, "Masjide Quba")
        self.assertEqual(req_obj.applicant_name, "Mohammad Irshad")
        self.assertEqual(req_obj.previous_registered_contact, "+919011956596")
        self.assertEqual(req_obj.contact_whatsapp, "+919876543210")
        self.assertEqual(req_obj.status, AccountRecoveryRequest.Status.PENDING)

    def test_recovery_request_fails_if_previous_contact_mismatches(self):
        """Test 2: Submitting an incorrect previous registered contact number is rejected with HTTP 400."""
        payload = {
            "mosque_id": self.mosque_quba.id,
            "applicant_name": "Fake Admin",
            "previous_registered_contact": "+919999900000",
            "contact_whatsapp": "+919876543210",
        }
        res = self.client.post(self.public_recovery_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("previous_registered_contact", res.data)
        self.assertIn("does not match", res.data["previous_registered_contact"][0])

        # Verify NO pending request created
        self.assertFalse(AccountRecoveryRequest.objects.filter(contact_whatsapp="+919876543210").exists())

    def test_phone_formatting_differences_normalized_correctly(self):
        """Test 3: Phone numbers formatted with spaces/dashes normalize and pass previous contact check."""
        payload = {
            "mosque_id": self.mosque_quba.id,
            "applicant_name": "Mohammad Irshad",
            "previous_registered_contact": "+91 90119-56596",
            "contact_whatsapp": "+91 98765 43210",
        }
        res = self.client.post(self.public_recovery_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        req_obj = AccountRecoveryRequest.objects.get(pk=res.data["id"])
        self.assertEqual(req_obj.previous_registered_contact, "+919011956596")
        self.assertEqual(req_obj.contact_whatsapp, "+919876543210")

    def test_super_admin_can_list_and_filter_recovery_requests(self):
        """Test 4: Super Admin can list recovery requests and filter by status."""
        req1 = AccountRecoveryRequest.objects.create(
            mosque=self.mosque_quba,
            mosque_name="Masjide Quba",
            applicant_name="Mohammad Irshad",
            previous_registered_contact="+919011956596",
            contact_whatsapp="+919876543210",
            status=AccountRecoveryRequest.Status.PENDING,
        )
        req2 = AccountRecoveryRequest.objects.create(
            mosque=self.mosque_quba,
            mosque_name="Masjide Quba",
            applicant_name="Awaiz Ahmed",
            previous_registered_contact="+919011956596",
            contact_whatsapp="+919123456789",
            status=AccountRecoveryRequest.Status.APPROVED,
        )

        self.client.force_authenticate(user=self.super_admin)
        res = self.client.get(self.super_admin_list_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 2)
        self.assertEqual(res.data["pending_count"], 1)

        # Filter pending
        res_pending = self.client.get(f"{self.super_admin_list_url}?status=pending")
        self.assertEqual(res_pending.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_pending.data["results"]), 1)
        self.assertEqual(res_pending.data["results"][0]["id"], req1.id)

    def test_unauthorized_user_cannot_access_super_admin_recovery_api(self):
        """Test 5: Non-super-admins cannot access Super Admin recovery endpoints."""
        self.client.force_authenticate(user=self.user_normal)
        res = self.client.get(self.super_admin_list_url)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_super_admin_approval_updates_administrator_identity_and_official_mosque_contact(self):
        """Test 6: Super Admin approval updates administrator login identity AND official Mosque contact_phone and contact_email."""
        req = AccountRecoveryRequest.objects.create(
            mosque=self.mosque_quba,
            mosque_name="Masjide Quba",
            applicant_name="Mohammad Irshad",
            previous_registered_contact="+919011956596",
            contact_email="shanu@gmail.com",
            contact_whatsapp="+917877878778",
            status=AccountRecoveryRequest.Status.PENDING,
        )

        self.client.force_authenticate(user=self.super_admin)
        approve_url = reverse("platform-admin-recovery-approve", kwargs={"pk": req.id})
        res = self.client.post(approve_url, {
            "target_user_id": self.user_irshad.id,
            "new_mobile_number": "+917877878778",
            "review_notes": "Identity verified via trustee document.",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        req.refresh_from_db()
        self.assertEqual(req.status, AccountRecoveryRequest.Status.APPROVED)
        self.assertEqual(req.reviewed_by, self.super_admin)

        # 1. Target user username & profiles updated
        self.user_irshad.refresh_from_db()
        self.assertEqual(self.user_irshad.username, "+917877878778")
        self.city_admin.refresh_from_db()
        self.assertEqual(self.city_admin.mobile_number, "+917877878778")
        self.mosque_admin.refresh_from_db()
        self.assertEqual(self.mosque_admin.mobile_number, "+917877878778")

        # 2. Official Mosque contact fields updated
        self.mosque_quba.refresh_from_db()
        self.assertEqual(self.mosque_quba.contact_phone, "+917877878778")
        self.assertEqual(self.mosque_quba.contact_email, "shanu@gmail.com")

        # 3. Public Mosque Detail API reflects new contact
        public_mosque_url = reverse("mosque-detail", kwargs={"pk": self.mosque_quba.id})
        self.client.logout()
        res_public = self.client.get(public_mosque_url)
        self.assertEqual(res_public.status_code, status.HTTP_200_OK)
        self.assertEqual(res_public.data["contact_phone"], "+917877878778")

    def test_super_admin_can_reject_recovery_request_without_modifying_mosque(self):
        """Test 7: Super Admin can reject a recovery request, leaving Mosque contact unchanged."""
        self.mosque_quba.contact_phone = "+919011956596"
        self.mosque_quba.save()

        req = AccountRecoveryRequest.objects.create(
            mosque=self.mosque_quba,
            mosque_name="Masjide Quba",
            applicant_name="Fake User",
            previous_registered_contact="+919011956596",
            contact_whatsapp="+919000000000",
            status=AccountRecoveryRequest.Status.PENDING,
        )

        self.client.force_authenticate(user=self.super_admin)
        reject_url = reverse("platform-admin-recovery-reject", kwargs={"pk": req.id})
        res = self.client.post(reject_url, {
            "review_notes": "Unable to verify trustee identity.",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        req.refresh_from_db()
        self.assertEqual(req.status, AccountRecoveryRequest.Status.REJECTED)
        self.assertEqual(req.review_notes, "Unable to verify trustee identity.")

        # Mosque contact must remain unchanged
        self.mosque_quba.refresh_from_db()
        self.assertEqual(self.mosque_quba.contact_phone, "+919011956596")

    def test_stale_previous_contact_check_on_approval(self):
        """Test 8: Approval is blocked with 409 Conflict if current Mosque contact changed since request creation."""
        req = AccountRecoveryRequest.objects.create(
            mosque=self.mosque_quba,
            mosque_name="Masjide Quba",
            applicant_name="Mohammad Irshad",
            previous_registered_contact="+919011956596",
            contact_whatsapp="+917877878778",
            status=AccountRecoveryRequest.Status.PENDING,
        )

        # Mosque contact gets updated out-of-band by another admin
        self.mosque_quba.contact_phone = "+917999999999"
        self.mosque_quba.save()

        self.client.force_authenticate(user=self.super_admin)
        approve_url = reverse("platform-admin-recovery-approve", kwargs={"pk": req.id})
        res = self.client.post(approve_url, {"new_mobile_number": "+917877878778"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("contact number has changed", res.data["detail"])

    def test_concurrent_approve_then_reject_returns_409_conflict(self):
        """Test 9: Stale Browser B attempting to reject an already APPROVED request receives HTTP 409 Conflict."""
        req = AccountRecoveryRequest.objects.create(
            mosque=self.mosque_quba,
            mosque_name="Masjide Quba",
            applicant_name="Mohammad Irshad",
            previous_registered_contact="+919011956596",
            contact_whatsapp="+919876543210",
            status=AccountRecoveryRequest.Status.PENDING,
        )

        self.client.force_authenticate(user=self.super_admin)
        approve_url = reverse("platform-admin-recovery-approve", kwargs={"pk": req.id})
        reject_url = reverse("platform-admin-recovery-reject", kwargs={"pk": req.id})

        # Browser A Approves
        res_a = self.client.post(approve_url, {"new_mobile_number": "+919876543210"}, format="json")
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)

        # Stale Browser B attempts Reject
        res_b = self.client.post(reject_url, {"review_notes": "Stale reject attempt"}, format="json")
        self.assertEqual(res_b.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already been processed", res_b.data["detail"])

        # DB must remain APPROVED
        req.refresh_from_db()
        self.assertEqual(req.status, AccountRecoveryRequest.Status.APPROVED)

    def test_concurrent_reject_then_approve_returns_409_conflict(self):
        """Test 10: Stale Browser B attempting to approve an already REJECTED request receives HTTP 409 Conflict."""
        req = AccountRecoveryRequest.objects.create(
            mosque=self.mosque_quba,
            mosque_name="Masjide Quba",
            applicant_name="Mohammad Irshad",
            previous_registered_contact="+919011956596",
            contact_whatsapp="+919876543210",
            status=AccountRecoveryRequest.Status.PENDING,
        )

        self.client.force_authenticate(user=self.super_admin)
        approve_url = reverse("platform-admin-recovery-approve", kwargs={"pk": req.id})
        reject_url = reverse("platform-admin-recovery-reject", kwargs={"pk": req.id})

        # Browser A Rejects
        res_a = self.client.post(reject_url, {"review_notes": "Rejected by A"}, format="json")
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)

        # Stale Browser B attempts Approve
        res_b = self.client.post(approve_url, {"new_mobile_number": "+919876543210"}, format="json")
        self.assertEqual(res_b.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already been processed", res_b.data["detail"])

        # DB must remain REJECTED
        req.refresh_from_db()
        self.assertEqual(req.status, AccountRecoveryRequest.Status.REJECTED)

    def test_reopen_rejected_request_transitions_to_pending(self):
        """Test 11: Super Admin reopens a REJECTED request, transitioning status to PENDING and recording reopen metadata."""
        req = AccountRecoveryRequest.objects.create(
            mosque=self.mosque_quba,
            mosque_name="Masjide Quba",
            applicant_name="Mohammad Irshad",
            previous_registered_contact="+919011956596",
            contact_whatsapp="+919876543210",
            status=AccountRecoveryRequest.Status.REJECTED,
            review_notes="Initial accidental rejection",
        )

        self.client.force_authenticate(user=self.super_admin)
        reopen_url = reverse("platform-admin-recovery-reopen", kwargs={"pk": req.id})
        res = self.client.post(reopen_url, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        req.refresh_from_db()
        self.assertEqual(req.status, AccountRecoveryRequest.Status.PENDING)
        self.assertEqual(req.reopened_by, self.super_admin)
        self.assertIsNotNone(req.reopened_at)
        # Previous rejection notes preserved
        self.assertEqual(req.review_notes, "Initial accidental rejection")

    def test_cannot_reopen_approved_or_pending_request(self):
        """Test 12: Attempting to reopen a PENDING or APPROVED request returns HTTP 409 Conflict."""
        req = AccountRecoveryRequest.objects.create(
            mosque=self.mosque_quba,
            mosque_name="Masjide Quba",
            applicant_name="Mohammad Irshad",
            previous_registered_contact="+919011956596",
            contact_whatsapp="+919876543210",
            status=AccountRecoveryRequest.Status.PENDING,
        )

        self.client.force_authenticate(user=self.super_admin)
        reopen_url = reverse("platform-admin-recovery-reopen", kwargs={"pk": req.id})
        res = self.client.post(reopen_url, format="json")
        self.assertEqual(res.status_code, status.HTTP_409_CONFLICT)

    def test_unregistered_mosque_recovery_submission_fails(self):
        """Test 13: Submitting account recovery for an unregistered mosque is rejected with HTTP 400 Bad Request."""
        payload = {
            "mosque_name": "Random Nonexistent Mosque XYZ",
            "applicant_name": "Fake Admin",
            "previous_registered_contact": "+919011956596",
            "contact_whatsapp": "+919876543210",
        }
        res = self.client.post(self.public_recovery_url, payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mosque_name", res.data)
        self.assertIn("not registered", res.data["mosque_name"][0])

    def test_old_phone_login_fails_and_new_phone_login_succeeds_after_recovery(self):
        """Test 14: Old phone login fails, new phone login succeeds, and all models/roles remain synchronized on single User."""
        from rest_framework.authtoken.models import Token
        old_token = Token.objects.create(user=self.user_irshad)

        req = AccountRecoveryRequest.objects.create(
            mosque=self.mosque_quba,
            mosque_name="Masjide Quba",
            applicant_name="Mohammad Irshad",
            previous_registered_contact="+919011956596",
            contact_email="irshad@example.com",
            contact_whatsapp="+917877878778",
            status=AccountRecoveryRequest.Status.PENDING,
        )

        self.client.force_authenticate(user=self.super_admin)
        approve_url = reverse("platform-admin-recovery-approve", kwargs={"pk": req.id})
        res_approve = self.client.post(approve_url, {
            "new_mobile_number": "+917877878778",
            "review_notes": "Approved for testing.",
        }, format="json")
        self.assertEqual(res_approve.status_code, status.HTTP_200_OK)

        self.client.logout()
        login_url = reverse("auth-login")

        # 1. Old phone + old password MUST FAIL
        res_old_login = self.client.post(login_url, {
            "mobile_number": "+919011956596",
            "password": "UserPassword123!",
        }, format="json")
        self.assertEqual(res_old_login.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. New phone + old password MUST SUCCEED
        res_new_login = self.client.post(login_url, {
            "mobile_number": "+917877878778",
            "password": "UserPassword123!",
        }, format="json")
        self.assertEqual(res_new_login.status_code, status.HTTP_200_OK)
        self.assertIn("token", res_new_login.data)

        # 3. Model synchronization verification
        self.user_irshad.refresh_from_db()
        self.city_admin.refresh_from_db()
        self.mosque_admin.refresh_from_db()
        self.mosque_quba.refresh_from_db()

        self.assertEqual(self.user_irshad.username, "+917877878778")
        self.assertEqual(self.mosque_admin.mobile_number, "+917877878778")
        self.assertEqual(self.city_admin.mobile_number, "+917877878778")
        self.assertEqual(self.mosque_quba.contact_phone, "+917877878778")
        self.assertEqual(self.mosque_quba.contact_email, "irshad@example.com")

        # 4. Same User object preserved for both roles, no duplicate created
        self.assertEqual(self.city_admin.user, self.user_irshad)
        self.assertEqual(self.mosque_admin.user, self.user_irshad)
        self.assertEqual(User.objects.filter(username="+917877878778").count(), 1)
        self.assertEqual(User.objects.filter(username="+919011956596").count(), 0)

        # 5. Old token invalidated
        self.assertFalse(Token.objects.filter(pk=old_token.pk).exists())

    def test_forgot_password_otp_behavior_after_recovery(self):
        """Test 15: Forgot password OTP flow starts for new phone and fails for old phone after recovery."""
        req = AccountRecoveryRequest.objects.create(
            mosque=self.mosque_quba,
            mosque_name="Masjide Quba",
            applicant_name="Mohammad Irshad",
            previous_registered_contact="+919011956596",
            contact_whatsapp="+917877878778",
            status=AccountRecoveryRequest.Status.PENDING,
        )

        self.client.force_authenticate(user=self.super_admin)
        approve_url = reverse("platform-admin-recovery-approve", kwargs={"pk": req.id})
        self.client.post(approve_url, {"new_mobile_number": "+917877878778"}, format="json")
        self.client.logout()

        forgot_url = reverse("auth-forgot-password-request")

        # 1. New phone starts OTP flow
        res_new_otp = self.client.post(forgot_url, {"mobile_number": "+917877878778"}, format="json")
        self.assertEqual(res_new_otp.status_code, status.HTTP_200_OK)

        # 2. Old phone fails immediately with HTTP 400
        res_old_otp = self.client.post(forgot_url, {"mobile_number": "+919011956596"}, format="json")
        self.assertEqual(res_old_otp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Account not found", res_old_otp.data["mobile_number"][0])

    def test_forgot_password_non_existent_phone_returns_400_and_creates_no_otp(self):
        """Test 16: Forgot password for non-existent phone returns HTTP 400 and creates no OTP challenge/delivery."""
        from apps.accounts.models import OTPVerification

        forgot_url = reverse("auth-forgot-password-request")
        payload = {"mobile_number": "+919999911111"}
        res = self.client.post(forgot_url, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mobile_number", res.data)
        self.assertIn("Account not found", res.data["mobile_number"][0])

        # Verify no OTP created
        self.assertEqual(OTPVerification.objects.filter(mobile_number="+919999911111").count(), 0)
