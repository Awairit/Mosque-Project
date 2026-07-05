import io
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.locations.models import City, CityDailyPrayerTiming
from apps.platform_admin.services import TimetableParser


class TimetableImporterTests(APITestCase):
    def setUp(self):
        self.super_user = User.objects.create_superuser(
            username="superadmin",
            password="superpassword",
            email="super@mosquefinder.org"
        )
        self.city = City.objects.create(
            name="Mumbai",
            latitude="19.076000",
            longitude="72.877700",
            timezone="Asia/Kolkata"
        )
        self.preview_url = reverse("platform-admin-cities-timetables", kwargs={"pk": self.city.pk, "action": "preview"})
        self.import_url = reverse("platform-admin-cities-timetables", kwargs={"pk": self.city.pk, "action": "import"})

    def test_parser_header_aliases_and_valid_csv(self):
        csv_data = (
            "Date,Fajar,Sunrise,Zuhr,Asar,Magrib,Esha\n"
            "2026-01-01,05:45,07:00,12:30,15:45,18:15,19:30\n"
            "2026-01-02,05:46,07:01,12:31,15:46,18:16,19:31\n"
        )
        file_obj = SimpleUploadedFile("timetable.csv", csv_data.encode("utf-8"), content_type="text/csv")
        records, errors, warnings, _, _ = TimetableParser.parse_file(file_obj, 2026, "Mumbai")
        
        self.assertEqual(len(records), 2)
        self.assertEqual(len(errors), 0)
        self.assertEqual(records[0]["date"], "2026-01-01")
        self.assertEqual(records[0]["fajr_time"], "05:45:00")
        self.assertEqual(records[0]["dhuhr_time"], "12:30:00")
        self.assertEqual(records[0]["maghrib_time"], "18:15:00")
        self.assertEqual(records[0]["isha_time"], "19:30:00")

    def test_parser_leap_year_handling(self):
        # 2024 is a leap year, so Feb 29 is valid
        csv_2024 = (
            "Date,Fajr,Sunrise,Dhuhr,Asr,Maghrib,Isha\n"
            "2024-02-29,05:45,07:00,12:30,15:45,18:15,19:30\n"
        )
        file_2024 = SimpleUploadedFile("leap.csv", csv_2024.encode("utf-8"), content_type="text/csv")
        records, errors, warnings, _, _ = TimetableParser.parse_file(file_2024, 2024, "Mumbai")
        self.assertEqual(len(records), 1)
        self.assertEqual(len(errors), 0)

        # 2025 is not a leap year, so a row explicitly claiming 2025-02-29 is a hard validation error
        csv_2025 = (
            "Date,Fajr,Sunrise,Dhuhr,Asr,Maghrib,Isha\n"
            "2025-02-29,05:45,07:00,12:30,15:45,18:15,19:30\n"
        )
        file_2025 = SimpleUploadedFile("nonleap.csv", csv_2025.encode("utf-8"), content_type="text/csv")
        records, errors, warnings, _, _ = TimetableParser.parse_file(file_2025, 2025, "Mumbai")
        self.assertEqual(len(records), 0)
        self.assertEqual(len(errors), 1)
        self.assertIn("Invalid Date", errors[0])

        # Feb 29 in a reusable template (e.g. 29-Feb) when importing for 2026 (non-leap) is an info skip warning, not an error
        csv_template = (
            "Date,Fajr,Sunrise,Dhuhr,Asr,Maghrib,Isha\n"
            "29-Feb,05:45,07:00,12:30,15:45,18:15,19:30\n"
        )
        file_template = SimpleUploadedFile("template.csv", csv_template.encode("utf-8"), content_type="text/csv")
        records, errors, warnings, _, _ = TimetableParser.parse_file(file_template, 2026, "Mumbai")
        self.assertEqual(len(records), 0)
        self.assertEqual(len(errors), 0) # NO ERRORS!
        self.assertEqual(len(warnings), 1)
        self.assertTrue(any("Skipped February 29 row" in w for w in warnings))

    def test_parser_year_and_city_warnings(self):
        csv_data = (
            "Date,Fajr,Sunrise,Dhuhr,Asr,Maghrib,Isha,City\n"
            "2025-01-01,05:45,07:00,12:30,15:45,18:15,19:30,Pune\n"
        )
        file_obj = SimpleUploadedFile("warn.csv", csv_data.encode("utf-8"), content_type="text/csv")
        records, errors, warnings, _, _ = TimetableParser.parse_file(file_obj, 2026, "Mumbai")
        
        self.assertEqual(len(records), 1)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(warnings), 2)
        self.assertTrue(any("differs from selected upload year" in w for w in warnings))
        self.assertTrue(any("differs from selected city" in w for w in warnings))

    def test_parser_format_b_month_day(self):
        csv_data = (
            "Month,Day,Fajr,Sunrise,Dhuhr,Asr,Maghrib,Isha\n"
            "January,15,05:45,07:00,12:30,15:45,18:15,19:30\n"
            "2,29,05:45,07:00,12:30,15:45,18:15,19:30\n" # invalid Feb 29 for 2026
        )
        file_obj = SimpleUploadedFile("format_b.csv", csv_data.encode("utf-8"), content_type="text/csv")
        records, errors, warnings, _, _ = TimetableParser.parse_file(file_obj, 2026, "Mumbai")
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["date"], "2026-01-15")
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Skipped February 29 row", warnings[0])

    def test_parser_error_collection_and_blank_rows(self):
        csv_data = (
            "Date,Fajr,Sunrise,Dhuhr,Asr,Maghrib,Isha\n"
            "2026-01-01,26:00,07:00,12:30,15:45,18:15,19:30\n" # invalid time
            "\n" # blank row to skip
            "2026-01-02,05:45,07:00,abcd,15:45,18:15,19:30\n" # invalid time
        )
        file_obj = SimpleUploadedFile("errors.csv", csv_data.encode("utf-8"), content_type="text/csv")
        records, errors, warnings, _, _ = TimetableParser.parse_file(file_obj, 2026, "Mumbai")
        
        self.assertEqual(len(records), 0)
        self.assertEqual(len(errors), 2)
        self.assertIn("Invalid Fajr time", errors[0])
        self.assertIn("Invalid Dhuhr time", errors[1])

    def test_api_preview_endpoint(self):
        self.client.force_authenticate(user=self.super_user)
        csv_data = (
            "Date,Fajr,Sunrise,Dhuhr,Asr,Maghrib,Isha\n"
            "2026-01-01,05:45,07:00,12:30,15:45,18:15,19:30\n"
        )
        file_obj = SimpleUploadedFile("preview.csv", csv_data.encode("utf-8"), content_type="text/csv")
        
        response = self.client.post(self.preview_url, {"file": file_obj, "year": "2026"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["valid_rows"], 1)
        self.assertEqual(response.data["invalid_rows"], 0)
        self.assertEqual(len(response.data["errors"]), 0)

    def test_api_import_replace_mode(self):
        # Create an existing timing
        CityDailyPrayerTiming.objects.create(
            city=self.city,
            date="2026-01-01",
            fajr_time="05:00:00",
            sunrise_time="06:30:00",
            dhuhr_time="12:00:00",
            asr_time="15:00:00",
            maghrib_time="18:00:00",
            isha_time="19:00:00"
        )

        self.client.force_authenticate(user=self.super_user)
        csv_data = (
            "Date,Fajr,Sunrise,Dhuhr,Asr,Maghrib,Isha\n"
            "2026-01-01,05:45,07:00,12:30,15:45,18:15,19:30\n"
            "2026-01-02,05:46,07:01,12:31,15:46,18:16,19:31\n"
        )
        file_obj = SimpleUploadedFile("import_replace.csv", csv_data.encode("utf-8"), content_type="text/csv")
        
        # Test conflict without overwrite
        response = self.client.post(self.import_url, {"file": file_obj, "year": "2026"})
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        
        # Test import with overwrite in Replace mode
        file_obj.seek(0)
        response = self.client.post(self.import_url, {"file": file_obj, "year": "2026", "overwrite": "true", "import_mode": "replace"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CityDailyPrayerTiming.objects.filter(city=self.city, date__year=2026).count(), 2)
        
        # Verify the record was replaced
        t1 = CityDailyPrayerTiming.objects.get(city=self.city, date="2026-01-01")
        self.assertEqual(t1.fajr_time.strftime("%H:%M:%S"), "05:45:00")

    def test_api_import_merge_mode(self):
        # Create an existing timing (2026-01-01)
        CityDailyPrayerTiming.objects.create(
            city=self.city,
            date="2026-01-01",
            fajr_time="05:00:00",
            sunrise_time="06:30:00",
            dhuhr_time="12:00:00",
            asr_time="15:00:00",
            maghrib_time="18:00:00",
            isha_time="19:00:00"
        )
        # Create another timing not in the file (2026-01-03)
        CityDailyPrayerTiming.objects.create(
            city=self.city,
            date="2026-01-03",
            fajr_time="05:10:00",
            sunrise_time="06:40:00",
            dhuhr_time="12:10:00",
            asr_time="15:10:00",
            maghrib_time="18:10:00",
            isha_time="19:10:00"
        )

        self.client.force_authenticate(user=self.super_user)
        csv_data = (
            "Date,Fajr,Sunrise,Dhuhr,Asr,Maghrib,Isha\n"
            "2026-01-01,05:45,07:00,12:30,15:45,18:15,19:30\n"
            "2026-01-02,05:46,07:01,12:31,15:46,18:16,19:31\n"
        )
        file_obj = SimpleUploadedFile("import_merge.csv", csv_data.encode("utf-8"), content_type="text/csv")
        
        # Merge import
        response = self.client.post(self.import_url, {"file": file_obj, "year": "2026", "overwrite": "true", "import_mode": "merge"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Under merge mode, 2026-01-01 is updated, 2026-01-02 is inserted, and 2026-01-03 remains untouched.
        # Total timings for the year should be 3
        self.assertEqual(CityDailyPrayerTiming.objects.filter(city=self.city, date__year=2026).count(), 3)
        
        # Verify 2026-01-01 was updated
        t1 = CityDailyPrayerTiming.objects.get(city=self.city, date="2026-01-01")
        self.assertEqual(t1.fajr_time.strftime("%H:%M:%S"), "05:45:00")
        
        # Verify 2026-01-03 was untouched
        t3 = CityDailyPrayerTiming.objects.get(city=self.city, date="2026-01-03")
        self.assertEqual(t3.fajr_time.strftime("%H:%M:%S"), "05:10:00")
