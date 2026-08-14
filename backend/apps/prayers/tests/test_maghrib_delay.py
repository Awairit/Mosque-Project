from datetime import date, time
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.locations.models import City, CityDailyPrayerTiming
from apps.mosques.models import Mosque
from apps.prayers.models import PrayerTiming
from apps.prayers.services import PrayerTimingService


class MaghribJamaatDelayTests(TestCase):
    """Targeted unit tests for RC-BUG-005 (Maghrib Jamaat Delay 1-30 mins) and RC-BUG-007 (Authoritative City Validation)."""

    def setUp(self):
        self.city = City.objects.create(
            name="Hyderabad",
            latitude=17.3850,
            longitude=78.4867,
            timezone="Asia/Kolkata",
            maghrib_auto_congregation_enabled=True,
            maghrib_congregation_offset=15,
        )
        self.mosque = Mosque.objects.create(
            mosque_name="Masjid Al-Noor",
            city="Hyderabad",
            city_relation=self.city,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        self.today = date.today()
        self.daily_timing = CityDailyPrayerTiming.objects.create(
            city=self.city,
            date=self.today,
            fajr_time=time(5, 0),
            sunrise_time=time(6, 0),
            dhuhr_time=time(12, 30),
            asr_time=time(16, 30),
            maghrib_time=time(18, 30),  # Sunset at 18:30
            isha_time=time(20, 0),
        )

    def test_maghrib_delay_dynamic_calculation(self):
        """Verify dynamic calculation: Sunset 18:30 + 7 min delay = 18:37 Jamaat time."""
        timing = PrayerTiming.objects.create(
            mosque=self.mosque,
            fajr_time=time(5, 15),
            dhuhr_time=time(12, 45),
            asr_time=time(16, 45),
            maghrib_time=time(18, 30),
            isha_time=time(20, 15),
            jumuah_time=time(13, 0),
            effective_from=self.today,
            maghrib_congregation_mode=PrayerTiming.CongregationMode.CITY_OFFSET,
            maghrib_delay_minutes=7,  # Configured 7 min delay after sunset
        )

        resolved = PrayerTimingService.resolve_timing(timing, self.today)
        self.assertEqual(resolved.maghrib_time, time(18, 37))
        self.assertEqual(resolved.maghrib_delay_minutes, 7)

    def test_maghrib_delay_validator_range(self):
        """Verify maghrib_delay_minutes enforces range between 1 and 30 minutes."""
        timing = PrayerTiming(
            mosque=self.mosque,
            fajr_time=time(5, 15),
            dhuhr_time=time(12, 45),
            asr_time=time(16, 45),
            maghrib_time=time(18, 30),
            isha_time=time(20, 15),
            jumuah_time=time(13, 0),
            effective_from=self.today,
            maghrib_delay_minutes=35,  # Exceeds max 30
        )
        with self.assertRaises(ValidationError):
            timing.full_clean()

    def test_authoritative_city_validation_on_registration(self):
        """Verify registration request rejects un-indexed imaginary cities."""
        from apps.mosques.serializers import MosqueRegistrationRequestSerializer

        # Valid city registration
        valid_data = {
            "mosque_name": "New Mosque",
            "admin_name": "Admin",
            "mobile_number": "+919876543210",
            "city": "Hyderabad",
            "address": "Street 1",
        }
        s_valid = MosqueRegistrationRequestSerializer(data=valid_data)
        self.assertTrue(s_valid.is_valid(), s_valid.errors)
        self.assertEqual(s_valid.validated_data["city_relation"], self.city)

        # Invalid imaginary city registration
        invalid_data = {
            "mosque_name": "Fake Mosque",
            "admin_name": "Admin",
            "mobile_number": "+919876543211",
            "city": "Imaginary Nonexistent City 999",
            "address": "Street 2",
        }
        s_invalid = MosqueRegistrationRequestSerializer(data=invalid_data)
        self.assertFalse(s_invalid.is_valid())
        self.assertIn("city", s_invalid.errors)
