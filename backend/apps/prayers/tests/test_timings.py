from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import MosqueAdmin
from apps.mosques.models import Mosque
from apps.prayers.models import PrayerTiming


class PrayerTimingAPITests(APITestCase):
    def setUp(self):
        # Create Mosque A and Admin A
        self.mosque_a = Mosque.objects.create(
            mosque_name="Mosque A",
            city="New York",
            address="123 Main St",
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        self.user_a = User.objects.create_user(
            username="1111111111", password="password123"
        )
        self.admin_a = MosqueAdmin.objects.create(
            user=self.user_a,
            mosque=self.mosque_a,
            mobile_number="1111111111",
            is_active=True,
        )

        # Create Mosque B and Admin B
        self.mosque_b = Mosque.objects.create(
            mosque_name="Mosque B",
            city="Boston",
            address="456 Elm St",
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        self.user_b = User.objects.create_user(
            username="2222222222", password="password123"
        )
        self.admin_b = MosqueAdmin.objects.create(
            user=self.user_b,
            mosque=self.mosque_b,
            mobile_number="2222222222",
            is_active=True,
        )

        self.timings_url = reverse("dashboard-prayer-timings")

    def test_get_timings_creates_default_record_for_authenticated_admin(self):
        self.client.force_authenticate(user=self.user_a)

        # Before request, no timings exist
        self.assertEqual(PrayerTiming.objects.count(), 0)

        response = self.client.get(self.timings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["fajr_time"], "05:00:00")
        self.assertEqual(response.data["jumuah_time"], "13:30:00")

        # After request, default timing should be created
        self.assertEqual(PrayerTiming.objects.count(), 1)
        timing = PrayerTiming.objects.first()
        self.assertEqual(timing.mosque, self.mosque_a)

    def test_update_timings_succeeds(self):
        self.client.force_authenticate(user=self.user_a)

        # Create initial record
        self.client.get(self.timings_url)

        # Perform update
        update_data = {
            "fajr_time": "05:15:00",
            "dhuhr_time": "13:45:00",
            "asr_time": "17:15:00",
            "maghrib_time": "19:15:00",
            "isha_time": "20:45:00",
            "jumuah_time": "13:45:00",
            "effective_from": "2026-06-01",
        }
        response = self.client.put(self.timings_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["fajr_time"], "05:15:00")
        self.assertEqual(response.data["dhuhr_time"], "13:45:00")
        self.assertEqual(response.data["updated_by_username"], self.user_a.username)

        # Verify DB changes
        timing = PrayerTiming.objects.get(mosque=self.mosque_a)
        self.assertEqual(timing.updated_by, self.user_a)

    def test_unauthorized_user_cannot_access_or_update(self):
        # GET is rejected
        response = self.client.get(self.timings_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # PUT is rejected
        response = self.client.put(self.timings_url, {"fajr_time": "05:15:00"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_mosque_isolation(self):
        # Set up timings for Mosque B by Admin B
        self.client.force_authenticate(user=self.user_b)
        self.client.get(self.timings_url)
        self.assertEqual(PrayerTiming.objects.filter(mosque=self.mosque_b).count(), 1)

        # Authenticate Admin A and verify they don't see or edit Mosque B's timings
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(self.timings_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that Mosque A has a new distinct record created and does not leak B's info
        self.assertNotEqual(response.data["mosque"], self.mosque_b.id)
        self.assertEqual(response.data["mosque"], self.mosque_a.id)

    def test_validation_failure_invalid_time(self):
        self.client.force_authenticate(user=self.user_a)
        self.client.get(self.timings_url)

        # Try to update with bad time string
        response = self.client.put(self.timings_url, {"fajr_time": "not-a-time"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("fajr_time", response.data)
