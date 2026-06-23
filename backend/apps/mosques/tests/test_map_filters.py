import datetime
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.mosques.models import Mosque, MosqueOperatingSchedule
from apps.prayers.models import PrayerTiming

class MosqueMapFiltersTests(APITestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(username="test_admin", password="password")

        # Create Mosque 1: Pune Central (has women space, parking, wudu, wheelchair, and jumuah timings)
        self.mosque_pune = Mosque.objects.create(
            mosque_name="Pune Central Masjid",
            city="Pune",
            address="Camp, Pune",
            latitude=18.520400,
            longitude=73.856700,
            women_prayer_available=True,
            parking_available=True,
            wudu_facility_available=True,
            wheelchair_accessible=True,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        
        # Set timings for Mosque 1 (enables Jumuah)
        self.timing_pune = PrayerTiming.objects.create(
            mosque=self.mosque_pune,
            fajr_time=datetime.time(5, 0),
            dhuhr_time=datetime.time(13, 30),
            asr_time=datetime.time(17, 0),
            maghrib_time=datetime.time(19, 0),
            isha_time=datetime.time(20, 30),
            jumuah_time=datetime.time(13, 30),
            effective_from=datetime.date.today(),
            updated_by=self.user,
        )

        # Create Mosque 2: Nanded Musallah (limited facilities, no Jumuah)
        self.mosque_nanded = Mosque.objects.create(
            mosque_name="Nanded Musallah",
            city="Nanded",
            address="Vazirabad, Nanded",
            latitude=19.150000,
            longitude=77.300000,
            women_prayer_available=False,
            parking_available=False,
            wudu_facility_available=False,
            wheelchair_accessible=False,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

    def test_bounding_box_filtering(self):
        url = reverse("mosque-list")
        
        # Viewport containing only Pune
        bbox_pune = "18.50,73.80,18.55,73.90"
        response = self.client.get(f"{url}?in_bbox={bbox_pune}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["mosque_name"], "Pune Central Masjid")

        # Viewport containing only Nanded
        bbox_nanded = "19.10,77.20,19.20,77.40"
        response = self.client.get(f"{url}?in_bbox={bbox_nanded}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["mosque_name"], "Nanded Musallah")

    def test_facility_filters(self):
        url = reverse("mosque-list")

        # 1. Filter: Women Space available
        response = self.client.get(f"{url}?women_prayer_available=true")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["mosque_name"], "Pune Central Masjid")

        # 2. Filter: Jumuah available
        response = self.client.get(f"{url}?jumuah_available=true")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["mosque_name"], "Pune Central Masjid")

        # 3. Filter: Parking and Wudu
        response = self.client.get(f"{url}?parking_available=true&wudu_facility_available=true")
        self.assertEqual(response.data["count"], 1)

    def test_open_now_filtering(self):
        # Configure operating schedule for Pune Central: Closed
        schedule = MosqueOperatingSchedule.objects.create(
            mosque=self.mosque_pune,
            open_24_hours=False,
            # Setup closed hours (empty/null implies closed, or set close times that are in the past/future)
            fajr_open=datetime.time(5, 0),
            fajr_close=datetime.time(6, 0),
            updated_by=self.user,
        )

        url = reverse("mosque-list")
        
        # Query Open Now -> Should return 0 results since Pune is closed and Nanded has no operating schedule (unverified defaults to closed in Availability Engine)
        response = self.client.get(f"{url}?open_now=true")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

        # Update Pune Central schedule to open 24 hours
        schedule.open_24_hours = True
        schedule.save()

        # Query Open Now -> Should return Pune Central Masjid
        response_open = self.client.get(f"{url}?open_now=true")
        self.assertEqual(response_open.status_code, status.HTTP_200_OK)
        self.assertEqual(response_open.data["count"], 1)
        self.assertEqual(response_open.data["results"][0]["mosque_name"], "Pune Central Masjid")
