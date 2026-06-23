import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.locations.models import City, CityPrayerTiming, CityDailyPrayerTiming, CityCalendarImportLog
from apps.locations.services import parse_and_validate_calendar_csv
from apps.mosques.models import Mosque
from apps.prayers.models import PrayerTiming


class CalendarImportServiceTests(TestCase):
    def setUp(self):
        self.city, _ = City.objects.get_or_create(name="Nanded", defaults={"latitude": 19.15, "longitude": 77.30})

    def test_valid_csv_parsing(self):
        csv_data = (
            "date,fajr_time,sunrise_time,dhuhr_time,asr_time,maghrib_time,isha_time\n"
            "2026-06-01,04:30:00,05:55:00,12:30:00,16:00:00,19:05:00,20:30:00\n"
            "2026-06-02,04:30:00,05:55:00,12:30:00,16:00:00,19:05:00,20:30:00\n"
        )
        result = parse_and_validate_calendar_csv(csv_data, self.city.id)
        self.assertTrue(result["success"])
        self.assertEqual(len(result["rows"]), 2)
        self.assertEqual(result["rows"][0]["date"], "2026-06-01")
        self.assertEqual(result["rows"][0]["fajr_time"], "04:30:00")

    def test_missing_headers_rejection(self):
        # Missing sunrise_time
        csv_data = (
            "date,fajr_time,dhuhr_time,asr_time,maghrib_time,isha_time\n"
            "2026-06-01,04:30:00,12:30:00,16:00:00,19:05:00,20:30:00\n"
        )
        result = parse_and_validate_calendar_csv(csv_data, self.city.id)
        self.assertFalse(result["success"])
        self.assertIn("Missing required columns in CSV headers", result["errors"][0])

    def test_invalid_date_format_rejection(self):
        csv_data = (
            "date,fajr_time,sunrise_time,dhuhr_time,asr_time,maghrib_time,isha_time\n"
            "06/01/2026,04:30:00,05:55:00,12:30:00,16:00:00,19:05:00,20:30:00\n"
        )
        result = parse_and_validate_calendar_csv(csv_data, self.city.id)
        self.assertFalse(result["success"])
        self.assertIn("Row 2: Invalid date format", result["errors"][0])

    def test_chronological_violation_fajr_sunrise(self):
        # Fajr time is after Sunrise
        csv_data = (
            "date,fajr_time,sunrise_time,dhuhr_time,asr_time,maghrib_time,isha_time\n"
            "2026-06-01,06:00:00,05:55:00,12:30:00,16:00:00,19:05:00,20:30:00\n"
        )
        result = parse_and_validate_calendar_csv(csv_data, self.city.id)
        self.assertFalse(result["success"])
        self.assertIn("Row 2: Fajr time (06:00) must be before Sunrise (05:55)", result["errors"][0])

    def test_chronological_violation_maghrib_isha(self):
        # Maghrib is after Isha
        csv_data = (
            "date,fajr_time,sunrise_time,dhuhr_time,asr_time,maghrib_time,isha_time\n"
            "2026-06-01,04:30:00,05:55:00,12:30:00,16:00:00,21:00:00,20:30:00\n"
        )
        result = parse_and_validate_calendar_csv(csv_data, self.city.id)
        self.assertFalse(result["success"])
        self.assertIn("Row 2: Maghrib time (21:00) must be before Isha (20:30)", result["errors"][0])


class CalendarImportAdminTests(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(username="admin", password="password", email="admin@test.com")
        self.city, _ = City.objects.get_or_create(name="Nanded", defaults={"latitude": 19.15, "longitude": 77.30})
        
        # Clear existing timings to keep it isolated
        CityPrayerTiming.objects.filter(city=self.city).delete()
        CityDailyPrayerTiming.objects.filter(city=self.city).delete()
        
        # Add baseline timing
        self.baseline = CityPrayerTiming.objects.create(
            city=self.city,
            calendar_date=None,
            fajr_time=datetime.time(4, 45),
            dhuhr_time=datetime.time(13, 0),
            asr_time=datetime.time(17, 0),
            maghrib_time=datetime.time(19, 0),
            isha_time=datetime.time(20, 30),
        )

    def test_anonymous_access_blocked(self):
        url = "/admin/locations/city/import-calendar/"
        response = self.client.get(url)
        # Should redirect to login
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_duplicate_import_protection_stats(self):
        self.client.login(username="admin", password="password")
        
        # Valid CSV calendar payload
        csv_data = (
            "date,fajr_time,sunrise_time,dhuhr_time,asr_time,maghrib_time,isha_time\n"
            "2026-06-01,04:30:00,05:55:00,12:30:00,16:00:00,19:05:00,20:30:00\n"
            "2026-06-02,04:30:00,05:55:00,12:30:00,16:00:00,19:05:00,20:30:00\n"
        )
        
        # 1. First Dry-run Upload
        url = "/admin/locations/city/import-calendar/"
        
        # We can construct a mock file upload
        import io
        file_obj = io.BytesIO(csv_data.encode("utf-8"))
        file_obj.name = "calendar.csv"
        
        response = self.client.post(url, {"city": self.city.id, "csv_file": file_obj, "validate": "Validate and Dry Run"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify preview stats
        self.assertContains(response, "Rows to Create")
        self.assertEqual(response.context["rows_created"], 2)
        self.assertEqual(response.context["rows_updated"], 0)
        self.assertEqual(response.context["rows_skipped"], 0)
        
        temp_filepath = response.context["temp_file"]
        
        # 2. Confirm and Commit Import
        response_commit = self.client.post(url, {
            "city_id": self.city.id,
            "temp_file": temp_filepath,
            "filename": "calendar.csv",
            "commit": "Confirm and Commit Import"
        })
        self.assertEqual(response_commit.status_code, status.HTTP_200_OK)
        
        # Verify db status counts
        log = CityCalendarImportLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.rows_created, 2)
        self.assertEqual(log.rows_updated, 0)
        self.assertEqual(log.rows_skipped, 0)
        
        # 3. Repeat identical import -> Verify skip protection count
        file_obj_dup = io.BytesIO(csv_data.encode("utf-8"))
        file_obj_dup.name = "calendar.csv"
        response_dup = self.client.post(url, {"city": self.city.id, "csv_file": file_obj_dup, "validate": "Validate and Dry Run"})
        self.assertEqual(response_dup.status_code, status.HTTP_200_OK)
        
        # Stats should show as skipped (unchanged)
        self.assertEqual(response_dup.context["rows_created"], 0)
        self.assertEqual(response_dup.context["rows_updated"], 0)
        self.assertEqual(response_dup.context["rows_skipped"], 2)
        
        # Commit second time
        temp_file_dup = response_dup.context["temp_file"]
        response_commit_dup = self.client.post(url, {
            "city_id": self.city.id,
            "temp_file": temp_file_dup,
            "filename": "calendar.csv",
            "commit": "Confirm and Commit Import"
        })
        self.assertEqual(response_commit_dup.status_code, status.HTTP_200_OK)
        
        # Verify second log
        second_log = CityCalendarImportLog.objects.all().order_by("-created_at").first()
        self.assertEqual(second_log.rows_created, 0)
        self.assertEqual(second_log.rows_updated, 0)
        self.assertEqual(second_log.rows_skipped, 2)

    def test_multi_year_coexistence(self):
        # Create timings for distinct years
        date_2026 = datetime.date(2026, 6, 1)
        date_2027 = datetime.date(2027, 6, 1)
        
        timing_2026 = CityDailyPrayerTiming.objects.create(
            city=self.city,
            date=date_2026,
            fajr_time=datetime.time(4, 30),
            sunrise_time=datetime.time(5, 55),
            dhuhr_time=datetime.time(12, 30),
            asr_time=datetime.time(16, 0),
            maghrib_time=datetime.time(19, 5),
            isha_time=datetime.time(20, 30),
        )
        
        timing_2027 = CityDailyPrayerTiming.objects.create(
            city=self.city,
            date=date_2027,
            fajr_time=datetime.time(4, 31),
            sunrise_time=datetime.time(5, 56),
            dhuhr_time=datetime.time(12, 31),
            asr_time=datetime.time(16, 1),
            maghrib_time=datetime.time(19, 6),
            isha_time=datetime.time(20, 31),
        )
        
        self.assertEqual(CityDailyPrayerTiming.objects.filter(city=self.city).count(), 2)


class CityTimingAPILookupTests(APITestCase):
    def setUp(self):
        self.city, _ = City.objects.get_or_create(name="Nanded", defaults={"latitude": 19.15, "longitude": 77.30})
        
        # Clear existing timings to keep it isolated
        CityPrayerTiming.objects.filter(city=self.city).delete()
        CityDailyPrayerTiming.objects.filter(city=self.city).delete()
        
        # Add baseline timing
        self.baseline = CityPrayerTiming.objects.create(
            city=self.city,
            calendar_date=None,
            fajr_time=datetime.time(4, 45),
            dhuhr_time=datetime.time(13, 0),
            asr_time=datetime.time(17, 0),
            maghrib_time=datetime.time(19, 0),
            isha_time=datetime.time(20, 30),
        )

    def test_api_prioritization_and_fallbacks(self):
        # 1. API fetch with no daily timing -> Should return baseline timing
        url = reverse("city-timings")
        response = self.client.get(f"{url}?city={self.city.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Returns baseline Fajr (04:45:00)
        self.assertEqual(response.data["fajr_time"], "04:45:00")
        self.assertNotIn("sunrise_time", response.data)

        # 2. Add daily timing for today
        today = datetime.date.today()
        daily = CityDailyPrayerTiming.objects.create(
            city=self.city,
            date=today,
            fajr_time=datetime.time(4, 30),
            sunrise_time=datetime.time(5, 55),
            dhuhr_time=datetime.time(12, 30),
            asr_time=datetime.time(16, 0),
            maghrib_time=datetime.time(19, 5),
            isha_time=datetime.time(20, 30),
        )

        # Re-fetch timings -> Should return daily timing with sunrise_time
        response_daily = self.client.get(f"{url}?city={self.city.id}")
        self.assertEqual(response_daily.status_code, status.HTTP_200_OK)
        # Returns daily Fajr (04:30:00) and Sunrise
        self.assertEqual(response_daily.data["fajr_time"], "04:30:00")
        self.assertEqual(response_daily.data["sunrise_time"], "05:55:00")
        
        # 3. Verify mosque independent timings are untouched
        mosque = Mosque.objects.create(
            mosque_name="Masjid-e-Faran",
            city="Nanded",
            address="Vazirabad",
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        mosque_timing = PrayerTiming.objects.create(
            mosque=mosque,
            fajr_time=datetime.time(5, 15),
            dhuhr_time=datetime.time(13, 45),
            asr_time=datetime.time(17, 30),
            maghrib_time=datetime.time(19, 10),
            isha_time=datetime.time(20, 45),
            jumuah_time=datetime.time(13, 30),
            effective_from=today,
        )
        
        # Verify mosque timing remains exactly as defined
        self.assertEqual(mosque.prayer_timing.fajr_time, datetime.time(5, 15))
        self.assertEqual(self.city.daily_prayer_timings.first().fajr_time, datetime.time(4, 30))
