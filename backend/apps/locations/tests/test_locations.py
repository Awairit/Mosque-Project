from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.locations.models import City, CityPrayerTiming


class LocationsAPITests(APITestCase):
    def setUp(self):
        # Clear database and seed test cities
        City.objects.all().delete()

        # Seed City 1: Pune
        self.pune = City.objects.create(
            name="Pune",
            latitude=18.5204,
            longitude=73.8567,
        )
        self.pune_timings = CityPrayerTiming.objects.create(
            city=self.pune,
            calendar_date=None,
            fajr_time="04:28:00",
            dhuhr_time="13:14:00",
            asr_time="17:37:00",
            maghrib_time="18:54:00",
            isha_time="20:11:00",
        )

        # Seed City 2: Nanded
        self.nanded = City.objects.create(
            name="Nanded",
            latitude=19.1383,
            longitude=77.3210,
        )
        self.nanded_timings = CityPrayerTiming.objects.create(
            city=self.nanded,
            calendar_date=None,
            fajr_time="04:32:00",
            dhuhr_time="13:18:00",
            asr_time="17:41:00",
            maghrib_time="18:58:00",
            isha_time="20:17:00",
        )

    def test_list_cities(self):
        url = reverse("city-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify it lists two seeded cities alphabetically (Nanded, Pune)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["results"][0]["name"], "Nanded")
        self.assertEqual(response.data["results"][1]["name"], "Pune")

    def test_get_city_timings_manual_selection_by_name(self):
        url = reverse("city-timings")
        response = self.client.get(url, {"city": "Pune"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city_details"]["name"], "Pune")
        self.assertEqual(response.data["fajr_time"], "04:28:00")

    def test_get_city_timings_manual_selection_by_id(self):
        url = reverse("city-timings")
        response = self.client.get(url, {"city": str(self.nanded.id)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city_details"]["name"], "Nanded")
        self.assertEqual(response.data["fajr_time"], "04:32:00")

    def test_get_city_timings_gps_detection(self):
        # Provide coordinates close to Pune
        url = reverse("city-timings")
        response = self.client.get(url, {"lat": "18.5000", "lon": "73.8000"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should auto-resolve to Pune
        self.assertEqual(response.data["city_details"]["name"], "Pune")

        # Provide coordinates close to Nanded
        response = self.client.get(url, {"lat": "19.1000", "lon": "77.3000"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should auto-resolve to Nanded
        self.assertEqual(response.data["city_details"]["name"], "Nanded")

    def test_get_city_timings_fallback_default(self):
        # If no params are passed, default is the first alphabetical city (Nanded)
        url = reverse("city-timings")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city_details"]["name"], "Nanded")
