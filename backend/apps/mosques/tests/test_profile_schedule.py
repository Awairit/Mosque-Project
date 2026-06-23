import datetime
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import MosqueAdmin
from apps.mosques.models import Mosque, MosqueOperatingSchedule


class MosqueProfileScheduleAPITests(APITestCase):
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

        self.profile_url = reverse("dashboard-mosque-profile")
        self.schedule_url = reverse("dashboard-operating-schedule")

    def test_profile_retrieval_and_update_succeeds(self):
        self.client.force_authenticate(user=self.user_a)

        # Get profile
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["mosque_name"], "Mosque A")

        # Update profile
        update_data = {
            "mosque_name": "Mosque A Updated",
            "description": "A peaceful place to pray.",
            "contact_phone": "555-1234",
            "website": "https://mosquea.org",
            "parking_available": True,
            "wudu_facility_available": True,
            "wheelchair_accessible": True,
            "mosque_type": Mosque.MosqueType.DAILY_PRAYER,
            "separate_women_entrance": True,
        }
        response = self.client.put(self.profile_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["mosque_name"], "Mosque A Updated")
        self.assertEqual(response.data["description"], "A peaceful place to pray.")
        self.assertTrue(response.data["parking_available"])
        self.assertEqual(response.data["mosque_type"], Mosque.MosqueType.DAILY_PRAYER)
        self.assertTrue(response.data["separate_women_entrance"])

        # Verify DB
        self.mosque_a.refresh_from_db()
        self.assertEqual(self.mosque_a.mosque_name, "Mosque A Updated")
        self.assertTrue(self.mosque_a.parking_available)

    def test_schedule_retrieval_returns_empty_by_default(self):
        self.client.force_authenticate(user=self.user_a)

        # Before GET, no schedule exists
        self.assertEqual(MosqueOperatingSchedule.objects.count(), 0)

        response = self.client.get(self.schedule_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["open_24_hours"])
        self.assertIsNone(response.data["fajr_open"])

        # After GET, empty schedule should exist in DB
        self.assertEqual(MosqueOperatingSchedule.objects.count(), 1)
        schedule = MosqueOperatingSchedule.objects.first()
        self.assertEqual(schedule.mosque, self.mosque_a)
        self.assertFalse(schedule.open_24_hours)
        self.assertIsNone(schedule.fajr_open)

    def test_schedule_update_succeeds(self):
        self.client.force_authenticate(user=self.user_a)

        # Create schedule
        self.client.get(self.schedule_url)

        # Update schedule to specify windows
        update_data = {
            "open_24_hours": False,
            "fajr_open": "04:30:00",
            "fajr_close": "06:00:00",
            "dhuhr_open": "12:30:00",
            "dhuhr_close": "14:30:00",
            "asr_open": "16:30:00",
            "asr_close": "18:00:00",
            "maghrib_open": "18:30:00",
            "maghrib_close": "20:00:00",
            "isha_open": "20:00:00",
            "isha_close": "22:00:00",
        }
        response = self.client.put(self.schedule_url, update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["fajr_open"], "04:30:00")
        self.assertEqual(response.data["updated_by_username"], self.user_a.username)

        # Verify DB changes
        schedule = MosqueOperatingSchedule.objects.get(mosque=self.mosque_a)
        self.assertEqual(schedule.fajr_open, datetime.time(4, 30))
        self.assertEqual(schedule.updated_by, self.user_a)

    def test_open_closed_status_calculation(self):
        schedule = MosqueOperatingSchedule.objects.create(
            mosque=self.mosque_a,
            open_24_hours=True,
        )

        # Case 1: Open 24 Hours
        status_info = schedule.get_current_status()
        self.assertTrue(status_info["is_open"])
        self.assertIsNone(status_info["opens_at"])
        self.assertIsNone(status_info["closes_at"])

        # Case 2: Empty schedule record
        schedule.open_24_hours = False
        schedule.save()
        status_info = schedule.get_current_status()
        self.assertFalse(status_info["is_open"])
        self.assertIn("message", status_info)
        self.assertEqual(status_info["message"], "No operating schedule configured yet.")

        # Case 3: Custom windows configured
        schedule.fajr_open = datetime.time(4, 30)
        schedule.fajr_close = datetime.time(6, 0)
        schedule.dhuhr_open = datetime.time(12, 30)
        schedule.dhuhr_close = datetime.time(14, 30)
        schedule.save()

        # Let's mock time or test by setting windows relative to current time
        import django.utils.timezone as django_timezone
        from zoneinfo import ZoneInfo
        from apps.locations.models import City

        city_obj, _ = City.objects.get_or_create(
            name="New York",
            defaults={"latitude": 40.7128, "longitude": -74.0060, "timezone": "America/New_York"}
        )
        
        now = django_timezone.now().astimezone(ZoneInfo(city_obj.timezone))
        current_time = now.time()

        # Set Fajr window to encompass current time
        # We need to construct times safely around current_time
        # Convert current time to minutes
        current_minutes = current_time.hour * 60 + current_time.minute
        
        # Fajr window: opens 10 minutes ago, closes 10 minutes from now
        open_minutes = (current_minutes - 10) % 1440
        close_minutes = (current_minutes + 10) % 1440
        
        schedule.fajr_open = datetime.time(open_minutes // 60, open_minutes % 60)
        schedule.fajr_close = datetime.time(close_minutes // 60, close_minutes % 60)
        schedule.save()

        if open_minutes < close_minutes:  # No midnight wrap
            status_info = schedule.get_current_status()
            self.assertTrue(status_info["is_open"])
            self.assertEqual(
                status_info["closes_at"],
                schedule.fajr_close.strftime("%I:%M %p")
            )

    def test_unauthorized_access(self):
        # Profile GET is rejected
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Profile PUT is rejected
        response = self.client.put(self.profile_url, {"mosque_name": "Attacker"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Schedule GET is rejected
        response = self.client.get(self.schedule_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Schedule PUT is rejected
        response = self.client.put(self.schedule_url, {"open_24_hours": True})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cross_mosque_isolation(self):
        # Log in as Admin A
        self.client.force_authenticate(user=self.user_a)

        # Verify GET returns Mosque A and not B
        response = self.client.get(self.profile_url)
        self.assertEqual(response.data["id"], self.mosque_a.id)
        self.assertNotEqual(response.data["id"], self.mosque_b.id)

        # Verify GET B's schedule from A's session yields A's schedule
        response = self.client.get(self.schedule_url)
        # Verify it created Mosque A's schedule
        self.assertEqual(response.data["mosque"], self.mosque_a.id)
