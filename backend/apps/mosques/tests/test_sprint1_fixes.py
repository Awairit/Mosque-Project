"""Automated verification and regression tests for MosqueCom V2 Sprint 1 Fixes:
- BUG-001: Side Effect Isolation (Zero synchronous external network calls during model save)
- BUG-002: Concurrent Mosque Registration Approval Race Condition (select_for_update + 409 Conflict)
- BUG-003: City Admin Content Scope Isolation & IDOR Protection (Unconditional mosque__isnull=True)
"""

import threading
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APITransactionTestCase

from apps.accounts.models import CityAdmin, MosqueAdmin
from apps.locations.models import City
from apps.mosques.models import Mosque, MosqueAnnouncement, MosqueEvent, MosqueRegistrationRequest


class Sprint1SideEffectIsolationTests(APITestCase):
    """BUG-001 Verification: Model saves must not execute synchronous external network calls."""

    def setUp(self):
        self.city = City.objects.create(
            name="Sprint1City",
            latitude=19.1383,
            longitude=77.3210,
            timezone="Asia/Kolkata"
        )
        self.mosque = Mosque.objects.create(
            mosque_name="Sprint1Mosque",
            city="Sprint1City",
            city_relation=self.city,
            address="123 Test Street",
            mosque_status=Mosque.MosqueStatus.ACTIVE
        )

    @patch("apps.common.services.notification.notification_service.send_whatsapp")
    def test_announcement_save_triggers_zero_synchronous_network_calls(self, mock_send_whatsapp):
        """Saving a published announcement must never trigger synchronous send_whatsapp."""
        announcement = MosqueAnnouncement.objects.create(
            mosque=self.mosque,
            city=self.city,
            title="Sprint 1 Announcement",
            content="Important congregation announcement.",
            announcement_type="general",
            priority="normal",
            status="published",
            is_active=True,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timezone.timedelta(days=7),
        )
        # Verify announcement persisted
        self.assertIsNotNone(announcement.id)
        # Assert send_whatsapp was NOT called
        mock_send_whatsapp.assert_not_called()

    @patch("apps.common.services.notification.notification_service.send_whatsapp")
    def test_event_save_triggers_zero_synchronous_network_calls(self, mock_send_whatsapp):
        """Saving a published event must never trigger synchronous send_whatsapp."""
        event = MosqueEvent.objects.create(
            mosque=self.mosque,
            city=self.city,
            title="Sprint 1 Event",
            description="Important event description.",
            event_type="lecture",
            status="published",
            is_active=True,
            event_date=timezone.localdate() + timezone.timedelta(days=2),
            event_time="19:00:00",
        )
        # Verify event persisted
        self.assertIsNotNone(event.id)
        # Assert send_whatsapp was NOT called
        mock_send_whatsapp.assert_not_called()


class Sprint1CityAdminScopeIDORTests(APITestCase):
    """BUG-003 Verification: City Admin Content Scope Isolation and IDOR Protection."""

    def setUp(self):
        self.city_aurangabad = City.objects.create(
            name="Aurangabad",
            latitude=19.8762,
            longitude=75.3433,
            timezone="Asia/Kolkata"
        )
        self.mosque_delhi_gate = Mosque.objects.create(
            mosque_name="Delhi Gate Masjid",
            city="Aurangabad",
            city_relation=self.city_aurangabad,
            address="Delhi Gate Road",
            mosque_status=Mosque.MosqueStatus.ACTIVE
        )

        # Create City Admin for Aurangabad
        self.city_admin_user = User.objects.create_user(
            username="+919888811111",
            password="Password123!",
            first_name="Aurangabad",
            last_name="Admin"
        )
        self.city_admin = CityAdmin.objects.create(
            user=self.city_admin_user,
            city=self.city_aurangabad,
            mobile_number="+919888811111",
            is_active=True
        )

        # Create Mosque Admin for Delhi Gate Masjid
        self.mosque_admin_user = User.objects.create_user(
            username="+919888822222",
            password="Password123!",
            first_name="Mosque",
            last_name="Admin"
        )
        self.mosque_admin = MosqueAdmin.objects.create(
            user=self.mosque_admin_user,
            mosque=self.mosque_delhi_gate,
            mobile_number="+919888822222",
            is_active=True
        )

        # Create a private Mosque-Scoped Announcement (mosque is set)
        self.mosque_announcement = MosqueAnnouncement.objects.create(
            mosque=self.mosque_delhi_gate,
            city=self.city_aurangabad,
            title="Mosque Committee Internal Notice",
            content="Exclusive to Delhi Gate Masjid attendees.",
            announcement_type="general",
            priority="normal",
            status="published",
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timezone.timedelta(days=5),
            created_by=self.mosque_admin_user
        )

        # Create a private Mosque-Scoped Event (mosque is set)
        self.mosque_event = MosqueEvent.objects.create(
            mosque=self.mosque_delhi_gate,
            city=self.city_aurangabad,
            title="Delhi Gate Youth Halaqah",
            description="Weekly youth gathering at Delhi Gate.",
            event_type="dars",
            status="published",
            event_date=timezone.localdate() + timezone.timedelta(days=3),
            event_time="18:30:00",
            created_by=self.mosque_admin_user
        )

        # Create a legitimate City-Scoped Announcement (mosque is None)
        self.city_announcement = MosqueAnnouncement.objects.create(
            mosque=None,
            city=self.city_aurangabad,
            title="Aurangabad Central Eidgah Cleanliness Drive",
            content="City-wide initiative for all residents.",
            announcement_type="general",
            priority="important",
            status="published",
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timezone.timedelta(days=7),
            created_by=self.city_admin_user
        )

    def test_city_admin_cannot_retrieve_mosque_scoped_announcement(self):
        """City Admin GET on a Mosque-scoped announcement ID must return 404 Not Found."""
        self.client.force_authenticate(user=self.city_admin_user)
        url = reverse("city-admin-announcements-detail", args=[self.mosque_announcement.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_city_admin_cannot_update_mosque_scoped_announcement(self):
        """City Admin PUT/PATCH on a Mosque-scoped announcement ID must return 404 Not Found."""
        self.client.force_authenticate(user=self.city_admin_user)
        url = reverse("city-admin-announcements-detail", args=[self.mosque_announcement.id])
        response = self.client.patch(url, {"title": "Hacked Title"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify DB untouched
        self.mosque_announcement.refresh_from_db()
        self.assertEqual(self.mosque_announcement.title, "Mosque Committee Internal Notice")

    def test_city_admin_cannot_delete_mosque_scoped_announcement(self):
        """City Admin DELETE on a Mosque-scoped announcement ID must return 404 Not Found."""
        self.client.force_authenticate(user=self.city_admin_user)
        url = reverse("city-admin-announcements-detail", args=[self.mosque_announcement.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify record still exists in DB
        self.assertTrue(MosqueAnnouncement.objects.filter(id=self.mosque_announcement.id).exists())

    def test_city_admin_cannot_retrieve_mosque_scoped_event(self):
        """City Admin GET on a Mosque-scoped event ID must return 404 Not Found."""
        self.client.force_authenticate(user=self.city_admin_user)
        url = reverse("city-admin-events-detail", args=[self.mosque_event.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_city_admin_cannot_delete_mosque_scoped_event(self):
        """City Admin DELETE on a Mosque-scoped event ID must return 404 Not Found."""
        self.client.force_authenticate(user=self.city_admin_user)
        url = reverse("city-admin-events-detail", args=[self.mosque_event.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Verify event still exists in DB
        self.assertTrue(MosqueEvent.objects.filter(id=self.mosque_event.id).exists())

    def test_city_admin_legitimate_city_scoped_crud_succeeds(self):
        """City Admin can view, update, and delete legitimate city-scoped announcements."""
        self.client.force_authenticate(user=self.city_admin_user)
        url = reverse("city-admin-announcements-detail", args=[self.city_announcement.id])

        # Retrieve
        get_res = self.client.get(url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertEqual(get_res.data["title"], "Aurangabad Central Eidgah Cleanliness Drive")

        # Update
        patch_res = self.client.patch(url, {"title": "Updated Eidgah Drive"}, format="json")
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.city_announcement.refresh_from_db()
        self.assertEqual(self.city_announcement.title, "Updated Eidgah Drive")
        self.assertIsNone(self.city_announcement.mosque)

        # Delete
        del_res = self.client.delete(url)
        self.assertEqual(del_res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MosqueAnnouncement.objects.filter(id=self.city_announcement.id).exists())


class Sprint1RegistrationConcurrencyTests(APITransactionTestCase):
    """BUG-002 Verification: Multi-threaded and sequential concurrency tests for registration approvals."""

    def setUp(self):
        self.city = City.objects.create(
            name="ConcurrencyCity",
            latitude=19.1383,
            longitude=77.3210,
            timezone="Asia/Kolkata"
        )
        self.super_user = User.objects.create_superuser(
            username="+919000000001",
            password="SuperPassword123!",
            email="superadmin@mosquecom.local"
        )
        self.super_user_2 = User.objects.create_superuser(
            username="+919000000002",
            password="SuperPassword123!",
            email="superadmin2@mosquecom.local"
        )
        self.reg_request = MosqueRegistrationRequest.objects.create(
            mosque_name="ConcurrencyProofMasjid",
            city="ConcurrencyCity",
            city_relation=self.city,
            address="456 Main Road",
            mobile_number="+919111122223",
            email="concurrency@test.local",
            status=MosqueRegistrationRequest.Status.PENDING
        )
        self.approve_url = reverse("platform-admin-requests-approve", args=[self.reg_request.id])
        self.reject_url = reverse("platform-admin-requests-reject", args=[self.reg_request.id])

    def test_concurrent_registration_approvals_race_condition(self):
        """Simultaneous approval requests for the same registration request must result in:
        - Exactly 1 HTTP 200 OK
        - Exactly 1 HTTP 409 Conflict
        - Exactly 1 created Mosque record
        - Exactly 1 created MosqueAdmin profile
        """
        results = []

        def approve_request(user):
            from rest_framework.test import APIClient
            client = APIClient()
            client.force_authenticate(user=user)
            res = client.post(self.approve_url)
            results.append(res.status_code)
            connection.close()

        t1 = threading.Thread(target=approve_request, args=(self.super_user,))
        t2 = threading.Thread(target=approve_request, args=(self.super_user_2,))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Exactly 1 success (200) and 1 conflict (409)
        self.assertEqual(len(results), 2)
        self.assertIn(status.HTTP_200_OK, results)
        self.assertIn(status.HTTP_409_CONFLICT, results)

        # Database Invariant Checks
        self.assertEqual(
            Mosque.objects.filter(mosque_name="ConcurrencyProofMasjid").count(),
            1,
            "Duplicate Mosque records were created by concurrent approvals!"
        )
        created_user = User.objects.get(username="+919111122223")
        self.assertEqual(
            MosqueAdmin.objects.filter(user=created_user).count(),
            1,
            "Duplicate MosqueAdmin profiles were created!"
        )
        self.reg_request.refresh_from_db()
        self.assertEqual(self.reg_request.status, MosqueRegistrationRequest.Status.APPROVED)

    def test_repeated_approval_after_success_returns_409_conflict(self):
        """Submitting an approval on an already approved request must return 409 Conflict."""
        self.client.force_authenticate(user=self.super_user)
        first_res = self.client.post(self.approve_url)
        self.assertEqual(first_res.status_code, status.HTTP_200_OK)

        # Second attempt
        second_res = self.client.post(self.approve_url)
        self.assertEqual(second_res.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already been processed", second_res.data["detail"])

    def test_approval_after_rejection_returns_409_conflict(self):
        """Attempting to approve a rejected request must return 409 Conflict."""
        self.client.force_authenticate(user=self.super_user)
        reject_res = self.client.post(self.reject_url, {"reason": "Duplicate registration."}, format="json")
        self.assertEqual(reject_res.status_code, status.HTTP_200_OK)

        # Attempt approval
        approve_res = self.client.post(self.approve_url)
        self.assertEqual(approve_res.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already been processed", approve_res.data["detail"])

    def test_rejection_after_approval_returns_409_conflict(self):
        """Attempting to reject an approved request must return 409 Conflict."""
        self.client.force_authenticate(user=self.super_user)
        approve_res = self.client.post(self.approve_url)
        self.assertEqual(approve_res.status_code, status.HTTP_200_OK)

        # Attempt reject
        reject_res = self.client.post(self.reject_url, {"reason": "Too late to reject."}, format="json")
        self.assertEqual(reject_res.status_code, status.HTTP_409_CONFLICT)
        self.assertIn("already been processed", reject_res.data["detail"])
