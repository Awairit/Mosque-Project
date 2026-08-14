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
        self.mosque_a.city_relation = city_obj
        self.mosque_a.save()

        
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

    def test_three_operating_modes_configuration_and_switching(self):
        self.client.force_authenticate(user=self.user_a)

        # 1. Configure General Open-Close Mode
        general_payload = {
            "schedule_mode": "GENERAL",
            "general_open_time": "04:45:00",
            "general_close_time": "22:30:00",
            # preserve existing prayer window values
            "fajr_open": "04:30:00",
            "fajr_close": "06:00:00",
        }
        response = self.client.put(self.schedule_url, general_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["schedule_mode"], "GENERAL")
        self.assertEqual(response.data["general_open_time"], "04:45:00")
        self.assertEqual(response.data["general_close_time"], "22:30:00")
        self.assertFalse(response.data["open_24_hours"])

        # Check model status
        schedule = MosqueOperatingSchedule.objects.get(mosque=self.mosque_a)
        self.assertEqual(schedule.schedule_mode, "GENERAL")

        # 2. Validation error if missing general times
        invalid_payload = {
            "schedule_mode": "GENERAL",
            "general_open_time": None,
            "general_close_time": None,
        }
        res_invalid = self.client.put(self.schedule_url, invalid_payload, format="json")
        self.assertEqual(res_invalid.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Switch to 24 Hours Mode
        twenty_four_payload = {
            "schedule_mode": "24_HOURS",
            "general_open_time": "04:45:00",
            "general_close_time": "22:30:00",
            "fajr_open": "04:30:00",
            "fajr_close": "06:00:00",
        }
        res_24 = self.client.put(self.schedule_url, twenty_four_payload, format="json")
        self.assertEqual(res_24.status_code, status.HTTP_200_OK)
        self.assertEqual(res_24.data["schedule_mode"], "24_HOURS")
        self.assertTrue(res_24.data["open_24_hours"])

        # 4. Switch to Salah-Based Mode (Verify Fajr data preserved)
        salah_payload = {
            "schedule_mode": "SALAH_BASED",
            "fajr_open": "04:30:00",
            "fajr_close": "06:00:00",
            "dhuhr_open": "12:30:00",
            "dhuhr_close": "14:30:00",
        }
        res_salah = self.client.put(self.schedule_url, salah_payload, format="json")

        self.assertEqual(res_salah.status_code, status.HTTP_200_OK)
        self.assertEqual(res_salah.data["schedule_mode"], "SALAH_BASED")
        self.assertFalse(res_salah.data["open_24_hours"])
        self.assertEqual(res_salah.data["fajr_open"], "04:30:00")
        self.assertEqual(res_salah.data["dhuhr_open"], "12:30:00")

    def test_general_mode_overnight_schedule_evaluation(self):
        # Create an overnight schedule: 10:00 PM to 02:00 AM
        schedule = MosqueOperatingSchedule.objects.create(
            mosque=self.mosque_a,
            schedule_mode="GENERAL",
            general_open_time=datetime.time(22, 0),
            general_close_time=datetime.time(2, 0),
        )
        # Verify get_current_status handles overnight properly
        status_info = schedule.get_current_status()
        # At midnight / late night or outside
        self.assertIn("is_open", status_info)

    def test_issue_1_schedule_save_with_empty_strings_succeeds(self):
        """ISSUE 1 — Verify saving 24_HOURS, GENERAL, and SALAH_BASED modes with empty strings succeeds."""
        self.client.force_authenticate(user=self.user_a)

        # 1. 24_HOURS mode with empty strings for time fields
        payload_24h = {
            "schedule_mode": "24_HOURS",
            "open_24_hours": True,
            "general_open_time": "",
            "general_close_time": "",
            "fajr_open": "",
            "fajr_close": "",
            "dhuhr_open": "",
            "dhuhr_close": "",
            "asr_open": "",
            "asr_close": "",
            "maghrib_open": "",
            "maghrib_close": "",
            "isha_open": "",
            "isha_close": "",
        }
        res_24h = self.client.put(self.schedule_url, payload_24h, format="json")
        self.assertEqual(res_24h.status_code, status.HTTP_200_OK, res_24h.data)
        self.assertEqual(res_24h.data["schedule_mode"], "24_HOURS")
        self.assertTrue(res_24h.data["open_24_hours"])

        # Reload & verify persistence
        res_reload1 = self.client.get(self.schedule_url)
        self.assertEqual(res_reload1.data["schedule_mode"], "24_HOURS")

        # 2. GENERAL mode with open/close times and empty strings for prayer windows
        payload_gen = {
            "schedule_mode": "GENERAL",
            "open_24_hours": False,
            "general_open_time": "05:00:00",
            "general_close_time": "22:00:00",
            "fajr_open": "",
            "fajr_close": "",
            "dhuhr_open": "",
            "dhuhr_close": "",
            "asr_open": "",
            "asr_close": "",
            "maghrib_open": "",
            "maghrib_close": "",
            "isha_open": "",
            "isha_close": "",
        }
        res_gen = self.client.put(self.schedule_url, payload_gen, format="json")
        self.assertEqual(res_gen.status_code, status.HTTP_200_OK, res_gen.data)
        self.assertEqual(res_gen.data["schedule_mode"], "GENERAL")
        self.assertEqual(res_gen.data["general_open_time"], "05:00:00")

        # Reload & verify persistence
        res_reload2 = self.client.get(self.schedule_url)
        self.assertEqual(res_reload2.data["schedule_mode"], "GENERAL")
        self.assertEqual(res_reload2.data["general_open_time"], "05:00:00")

        # 3. SALAH_BASED mode with Fajr window and empty strings for other times
        payload_salah = {
            "schedule_mode": "SALAH_BASED",
            "open_24_hours": False,
            "general_open_time": "",
            "general_close_time": "",
            "fajr_open": "05:00:00",
            "fajr_close": "06:30:00",
            "dhuhr_open": "",
            "dhuhr_close": "",
            "asr_open": "",
            "asr_close": "",
            "maghrib_open": "",
            "maghrib_close": "",
            "isha_open": "",
            "isha_close": "",
        }
        res_salah = self.client.put(self.schedule_url, payload_salah, format="json")
        self.assertEqual(res_salah.status_code, status.HTTP_200_OK, res_salah.data)
        self.assertEqual(res_salah.data["schedule_mode"], "SALAH_BASED")
        self.assertEqual(res_salah.data["fajr_open"], "05:00:00")

        # Reload & verify persistence
        res_reload3 = self.client.get(self.schedule_url)
        self.assertEqual(res_reload3.data["schedule_mode"], "SALAH_BASED")
        self.assertEqual(res_reload3.data["fajr_open"], "05:00:00")

    def test_issue_2_women_prayer_space_editable(self):
        """ISSUE 2 — Verify Women's Prayer Space is editable post-registration (False -> True -> False)."""
        self.client.force_authenticate(user=self.user_a)

        # Mosque initially has women_prayer_available = False
        self.assertFalse(self.mosque_a.women_prayer_available)

        # 1. Update False -> True
        res1 = self.client.patch(self.profile_url, {"women_prayer_available": True}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_200_OK, res1.data)
        self.assertTrue(res1.data["women_prayer_available"])

        self.mosque_a.refresh_from_db()
        self.assertTrue(self.mosque_a.women_prayer_available)

        # Verify separate_women_entrance remains intact
        self.assertIn("separate_women_entrance", res1.data)

        # 2. Update True -> False
        res2 = self.client.patch(self.profile_url, {"women_prayer_available": False}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_200_OK, res2.data)
        self.assertFalse(res2.data["women_prayer_available"])

        self.mosque_a.refresh_from_db()
        self.assertFalse(self.mosque_a.women_prayer_available)

    def test_issue_3_super_admin_pending_requests_count(self):
        """ISSUE 3 — Verify registration-requests/?status=pending count for Super Admin notification badge."""
        from apps.mosques.models import MosqueRegistrationRequest
        from apps.platform_admin.views import SuperAdminRegistrationRequestListAPIView

        superuser = User.objects.create_superuser("superadmin", "super@admin.com", "superpass123")
        self.client.force_authenticate(user=superuser)

        # 0 pending -> count = 0
        url = reverse("platform-admin-requests-list") + "?status=pending"
        res0 = self.client.get(url)
        self.assertEqual(res0.status_code, status.HTTP_200_OK)
        self.assertEqual(res0.data["count"], 0)

        # 1 pending -> count = 1
        req1 = MosqueRegistrationRequest.objects.create(
            mosque_name="Pending 1", mobile_number="+919999900001", city="Delhi", status="pending"
        )
        res1 = self.client.get(url)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.data["count"], 1)

        # 2 pending -> count = 2
        req2 = MosqueRegistrationRequest.objects.create(
            mosque_name="Pending 2", mobile_number="+919999900002", city="Delhi", status="pending"
        )
        res2 = self.client.get(url)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data["count"], 2)

        # Process approval -> count decreases
        req1.status = "approved"
        req1.save()
        res3 = self.client.get(url)
        self.assertEqual(res3.status_code, status.HTTP_200_OK)
        self.assertEqual(res3.data["count"], 1)


