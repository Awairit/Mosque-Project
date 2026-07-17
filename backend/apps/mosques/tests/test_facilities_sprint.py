from django.test import TestCase
from rest_framework.test import APIClient
from apps.mosques.models import Mosque
from apps.mosques.serializers import MosqueSerializer, MosqueProfileSerializer


class FacilitiesSprintTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.mosque = Mosque.objects.create(
            mosque_name="Facilities Test Mosque",
            city="Nanded",
            address="VIP Road",
            women_prayer_available=True,
            parking_available=True,
            wudu_facility_available=True,
            wheelchair_accessible=True,
            drinking_water_available=True,
            washrooms_available=True,
            separate_women_entrance=True,
            funeral_prayer_facility_available=True,
        )

    def test_serializer_contains_all_17_facilities(self):
        serializer = MosqueSerializer(self.mosque)
        data = serializer.data

        expected_fields = [
            "women_prayer_available",
            "separate_women_entrance",
            "parking_available",
            "wudu_facility_available",
            "wheelchair_accessible",
            "drinking_water_available",
            "washrooms_available",
            "library_available",
            "quran_classes_available",
            "hifz_program_available",
            "nikah_service_available",
            "muslim_burial_ground_available",
            "community_hall_available",
            "ramadan_iftar_available",
            "eid_prayer_ground_available",
            "zakat_collection_available",
            "funeral_prayer_facility_available",
        ]

        for field in expected_fields:
            self.assertIn(field, data, f"Field '{field}' missing from MosqueSerializer")
            self.assertIsInstance(data[field], bool, f"Field '{field}' is not serialized as Boolean")

    def test_profile_serializer_contains_all_17_facilities(self):
        serializer = MosqueProfileSerializer(self.mosque)
        data = serializer.data

        expected_fields = [
            "women_prayer_available",
            "separate_women_entrance",
            "parking_available",
            "wudu_facility_available",
            "wheelchair_accessible",
            "drinking_water_available",
            "washrooms_available",
            "library_available",
            "quran_classes_available",
            "hifz_program_available",
            "nikah_service_available",
            "muslim_burial_ground_available",
            "community_hall_available",
            "ramadan_iftar_available",
            "eid_prayer_ground_available",
            "zakat_collection_available",
            "funeral_prayer_facility_available",
        ]

        for field in expected_fields:
            self.assertIn(field, data, f"Field '{field}' missing from MosqueProfileSerializer")

    def test_api_endpoint_returns_facilities(self):
        response = self.client.get(f"/api/v1/mosques/{self.mosque.id}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertTrue(data["women_prayer_available"])
        self.assertTrue(data["parking_available"])
        self.assertTrue(data["wudu_facility_available"])
        self.assertTrue(data["wheelchair_accessible"])
        self.assertTrue(data["drinking_water_available"])
        self.assertTrue(data["washrooms_available"])
        self.assertTrue(data["separate_women_entrance"])
        self.assertTrue(data["funeral_prayer_facility_available"])
        self.assertFalse(data["library_available"])
