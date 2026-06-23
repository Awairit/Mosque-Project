from datetime import time, datetime, date
from unittest.mock import patch
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.mosques.models import Mosque, MosqueOperatingSchedule
from apps.mosques.services import MosqueAvailabilityEngine
from apps.prayers.models import PrayerTiming


class MosqueAvailabilityAndDiscoveryTests(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(username="testadmin", password="password")

        # Create Mosque 1: Near (e.g. Pune)
        self.mosque_near = Mosque.objects.create(
            mosque_name="Near Mosque",
            city="Pune",
            address="Near Address",
            latitude=18.5204,
            longitude=73.8567,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

        # Create Mosque 2: Far (e.g. Nanded)
        self.mosque_far = Mosque.objects.create(
            mosque_name="Far Mosque",
            city="Nanded",
            address="Far Address",
            latitude=19.1383,
            longitude=77.3210,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

        # Timings for Near Mosque
        self.near_timing = PrayerTiming.objects.create(
            mosque=self.mosque_near,
            fajr_time=time(5, 0),
            dhuhr_time=time(13, 30),
            asr_time=time(17, 0),
            maghrib_time=time(18, 30),
            isha_time=time(20, 0),
            jumuah_time=time(13, 30),
            effective_from=timezone.now().date(),
            updated_by=self.user,
        )

        # Operating Schedule for Near Mosque (Specific Windows)
        self.near_schedule = MosqueOperatingSchedule.objects.create(
            mosque=self.mosque_near,
            open_24_hours=False,
            fajr_open=time(4, 45),
            fajr_close=time(9, 45),
            dhuhr_open=time(13, 15),
            dhuhr_close=time(15, 30),
            asr_open=time(16, 45),
            asr_close=time(18, 0),
            maghrib_open=time(18, 15),
            maghrib_close=time(19, 0),
            isha_open=time(19, 45),
            isha_close=time(21, 0),
            updated_by=self.user,
        )

    def test_availability_engine_open_status(self):
        # 1. Test Dhuhr Open Window (Reference Time: 2:00 PM)
        ref_dt = datetime.combine(timezone.now().date(), time(14, 0))
        engine = MosqueAvailabilityEngine(self.mosque_near, current_dt=ref_dt)
        avail = engine.get_availability()
        self.assertTrue(avail["is_open"])
        self.assertEqual(avail["status_label"], "Open Now")
        self.assertEqual(avail["current_window"], "dhuhr")
        self.assertEqual(avail["closes_at"], "03:30 PM")
        self.assertEqual(avail["next_prayer_name"], "Asr")

    def test_availability_engine_closing_soon_status(self):
        # 2. Test Closing Soon (Reference Time: 3:20 PM - window closes at 3:30 PM)
        ref_dt = datetime.combine(timezone.now().date(), time(15, 20))
        engine = MosqueAvailabilityEngine(self.mosque_near, current_dt=ref_dt)
        avail = engine.get_availability()
        self.assertTrue(avail["is_open"])
        self.assertEqual(avail["status_label"], "Closing Soon")
        self.assertEqual(avail["current_window"], "dhuhr")

    def test_availability_engine_closed_status(self):
        # 3. Test Closed state (Reference Time: 10:00 AM)
        ref_dt = datetime.combine(timezone.now().date(), time(10, 0))
        engine = MosqueAvailabilityEngine(self.mosque_near, current_dt=ref_dt)
        avail = engine.get_availability()
        self.assertFalse(avail["is_open"])
        self.assertEqual(avail["status_label"], "Closed")
        self.assertEqual(avail["opens_at"], "01:15 PM")  # Dhuhr opens next
        self.assertEqual(avail["next_prayer_name"], "Dhuhr")

    def test_availability_engine_rollover_tomorrow(self):
        # 4. Test Rollover (Reference Time: 10:00 PM - all windows passed)
        ref_dt = datetime.combine(timezone.now().date(), time(22, 0))
        engine = MosqueAvailabilityEngine(self.mosque_near, current_dt=ref_dt)
        avail = engine.get_availability()
        self.assertFalse(avail["is_open"])
        self.assertEqual(avail["status_label"], "Closed")
        self.assertEqual(avail["opens_at"], "04:45 AM")  # tomorrow's Fajr
        self.assertEqual(avail["next_prayer_name"], "Fajr")  # tomorrow's Fajr

    def test_availability_engine_unverified(self):
        # 5. Far Mosque has no schedule configured
        engine = MosqueAvailabilityEngine(self.mosque_far)
        avail = engine.get_availability()
        self.assertFalse(avail["is_open"])
        self.assertEqual(avail["status_label"], "Schedule Not Verified")

    def test_nearest_mosques_listing_with_coordinates(self):
        url = reverse("mosque-list")
        # Query near Pune (18.52, 73.85)
        response = self.client.get(url, {"lat": "18.5200", "lon": "73.8500"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Results should be ordered: Near Mosque, then Far Mosque
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["mosque_name"], "Near Mosque")
        self.assertEqual(results[1]["mosque_name"], "Far Mosque")
        # Verify distance is computed and attached
        self.assertIsNotNone(results[0]["distance"])
        self.assertIsNotNone(results[1]["distance"])
        self.assertLess(results[0]["distance"], results[1]["distance"])

    @patch("django.utils.timezone.now")
    def test_mosque_detail_endpoint(self, mock_now):
        # Mock timezone.now() to return 04:30 AM UTC, which converts to 10:00 AM IST (Asia/Kolkata)
        mock_dt = timezone.make_aware(datetime.combine(date(2026, 6, 1), time(4, 30)))
        mock_now.return_value = mock_dt

        url = reverse("mosque-detail", kwargs={"pk": self.mosque_near.id})
        response = self.client.get(url, {"lat": "18.5200", "lon": "73.8500"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["mosque_name"], "Near Mosque")
        # Exposes operating status and distance
        self.assertIsNotNone(response.data["distance"])
        self.assertEqual(response.data["operating_status"]["is_open"], False)
        self.assertEqual(response.data["operating_status"]["status_label"], "Closed")

    def test_multi_timezone_availability(self):
        from apps.locations.models import City
        from zoneinfo import ZoneInfo
        
        # Create cities with custom timezones
        dubai_city = City.objects.create(name="Dubai", latitude=25.2048, longitude=55.2708, timezone="Asia/Dubai")
        london_city = City.objects.create(name="London", latitude=51.5074, longitude=-0.1278, timezone="Europe/London")
        ny_city = City.objects.create(name="New York", latitude=40.7128, longitude=-74.0060, timezone="America/New_York")

        # Create mosques in those cities
        mosque_dubai = Mosque.objects.create(
            mosque_name="Dubai Mosque",
            city="Dubai",
            latitude=25.2048,
            longitude=55.2708,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        mosque_london = Mosque.objects.create(
            mosque_name="London Mosque",
            city="London",
            latitude=51.5074,
            longitude=-0.1278,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        mosque_ny = Mosque.objects.create(
            mosque_name="New York Mosque",
            city="New York",
            latitude=40.7128,
            longitude=-74.0060,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

        # Set schedules and prayer timings for these mosques
        for m in [mosque_dubai, mosque_london, mosque_ny]:
            MosqueOperatingSchedule.objects.create(
                mosque=m,
                open_24_hours=False,
                fajr_open=time(4, 45),
                fajr_close=time(9, 45),
                dhuhr_open=time(13, 15),
                dhuhr_close=time(15, 30),
                asr_open=time(15, 30),
                asr_close=time(18, 30),
                maghrib_open=time(19, 0),
                maghrib_close=time(20, 0),
                isha_open=time(20, 30),
                isha_close=time(21, 30),
            )
            PrayerTiming.objects.create(
                mosque=m,
                fajr_time=time(5, 15),
                dhuhr_time=time(13, 45),
                asr_time=time(17, 30),
                maghrib_time=time(19, 0),
                isha_time=time(20, 45),
                jumuah_time=time(13, 30),
                effective_from=timezone.now().date(),
            )

        import datetime as dt_module
        system_dt_utc = timezone.make_aware(datetime(2026, 6, 1, 11, 40, 0), timezone=dt_module.timezone.utc)

        # 1. Dubai local time: 11:40 UTC + 4 = 15:40 (03:40 PM). Inside Asr operating window (15:30 to 18:30).
        # Expected: Open Now, Next Congregation: Asr at 05:30 PM
        engine_dubai = MosqueAvailabilityEngine(mosque_dubai, current_dt=system_dt_utc)
        avail_dubai = engine_dubai.get_availability()
        self.assertTrue(avail_dubai["is_open"])
        self.assertEqual(avail_dubai["status_label"], "Open Now")
        self.assertEqual(avail_dubai["next_prayer_name"], "Asr")
        self.assertEqual(avail_dubai["next_prayer_time"], "05:30 PM")

        # 2. London local time: 11:40 UTC + 1 = 12:40 (12:40 PM). Closed, opens at 01:15 PM, Next Congregation: Dhuhr at 01:45 PM.
        engine_london = MosqueAvailabilityEngine(mosque_london, current_dt=system_dt_utc)
        avail_london = engine_london.get_availability()
        self.assertFalse(avail_london["is_open"])
        self.assertEqual(avail_london["status_label"], "Closed")
        self.assertEqual(avail_london["opens_at"], "01:15 PM")
        self.assertEqual(avail_london["next_prayer_name"], "Dhuhr")
        self.assertEqual(avail_london["next_prayer_time"], "01:45 PM")

        # 3. New York local time: 11:40 UTC - 4 = 07:40 (07:40 AM). Inside Fajr operating window (04:45 to 09:45).
        # Expected: Open Now, Next Congregation: Dhuhr at 01:45 PM (since Fajr jamaat was at 05:15 AM).
        engine_ny = MosqueAvailabilityEngine(mosque_ny, current_dt=system_dt_utc)
        avail_ny = engine_ny.get_availability()
        self.assertTrue(avail_ny["is_open"])
        self.assertEqual(avail_ny["status_label"], "Open Now")
        self.assertEqual(avail_ny["next_prayer_name"], "Dhuhr")
        self.assertEqual(avail_ny["next_prayer_time"], "01:45 PM")
