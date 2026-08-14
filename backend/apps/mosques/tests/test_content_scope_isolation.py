"""Automated tests for Content Scope Isolation (ROLE != CONTENT SCOPE) for Dual-Role users."""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import CityAdmin, MosqueAdmin
from apps.locations.models import City
from apps.mosques.models import Mosque, MosqueAnnouncement, MosqueEvent


class ContentScopeIsolationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.city_nanded, _ = City.objects.get_or_create(
            name="Nanded",
            defaults={"latitude": 19.1383, "longitude": 77.3210, "timezone": "Asia/Kolkata"}
        )
        self.city_hyderabad, _ = City.objects.get_or_create(
            name="Hyderabad",
            defaults={"latitude": 17.3850, "longitude": 78.4867, "timezone": "Asia/Kolkata"}
        )

        self.mosque_quba, _ = Mosque.objects.get_or_create(
            mosque_name="Masjide Quba",
            defaults={
                "city": "Nanded",
                "city_relation": self.city_nanded,
                "address": "Nanded Town",
                "mosque_status": Mosque.MosqueStatus.ACTIVE,
            }
        )
        self.mosque_aqsa, _ = Mosque.objects.get_or_create(
            mosque_name="Masjide Aqsa",
            defaults={
                "city": "Hyderabad",
                "city_relation": self.city_hyderabad,
                "address": "Hyderabad Town",
                "mosque_status": Mosque.MosqueStatus.ACTIVE,
            }
        )

        CityAdmin.objects.filter(city__in=[self.city_nanded, self.city_hyderabad]).delete()

        # Dual-Role User: Mohammad Irshad (City Admin Nanded + Mosque Admin Quba)
        self.user_irshad = User.objects.create_user(
            username="+919011956596",
            password="Password123!",
            first_name="Mohammad",
            last_name="Irshad",
        )
        self.city_admin_irshad = CityAdmin.objects.create(
            user=self.user_irshad,
            city=self.city_nanded,
            mobile_number="+919011956596",
            is_active=True,
        )
        self.mosque_admin_irshad = MosqueAdmin.objects.create(
            user=self.user_irshad,
            mosque=self.mosque_quba,
            mobile_number="+919011956596",
            is_active=True,
        )

        # Endpoints
        self.city_admin_announcements_url = reverse("city-admin-announcements-list")
        self.city_admin_events_url = reverse("city-admin-events-list")
        self.dashboard_announcements_url = reverse("dashboard-announcements-list")
        self.dashboard_events_url = reverse("dashboard-events-list")
        self.public_announcements_url = reverse("public-announcements-list")
        self.public_events_url = reverse("public-events-list")

    def test_city_notice_created_in_city_admin_context_is_city_scoped(self):
        """Test 1: Notice created in City Admin context -> Scope CITY (mosque=None) -> Appears in Nanded City Notice Board."""
        self.client.force_authenticate(user=self.user_irshad)
        today = timezone.localdate()
        next_week = today + timezone.timedelta(days=7)

        res = self.client.post(self.city_admin_announcements_url, {
            "title": "Nanded Road Update",
            "content": "Road construction update for Nanded.",
            "announcement_type": "general",
            "priority": "important",
            "status": "published",
            "start_date": str(today),
            "end_date": str(next_week),
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(res.data["mosque"])

        # Check Public City Notice Board
        self.client.logout()
        pub_res = self.client.get(f"{self.public_announcements_url}?city_id={self.city_nanded.id}")
        self.assertEqual(pub_res.status_code, status.HTTP_200_OK)
        items = pub_res.data["results"] if isinstance(pub_res.data, dict) and "results" in pub_res.data else pub_res.data
        titles = [i["title"] for i in items]
        self.assertIn("Nanded Road Update", titles)

        # Attribution verify
        target = [i for i in items if i["title"] == "Nanded Road Update"][0]
        self.assertIsNotNone(target["published_by"])
        self.assertEqual(target["published_by"]["name"], "Mohammad Irshad")
        self.assertEqual(target["published_by"]["role"], "City Administrator")

    def test_mosque_notice_created_in_my_mosque_context_does_not_leak_to_city_notice_board(self):
        """Test 2: Notice created in My Mosque context -> Scope MOSQUE (mosque=Quba) -> Appears on Quba Mosque, NOT Nanded City Notice Board."""
        self.client.force_authenticate(user=self.user_irshad)
        today = timezone.localdate()
        next_week = today + timezone.timedelta(days=7)

        res = self.client.post(self.dashboard_announcements_url, {
            "title": "Quba Road Block",
            "content": "Street blocked near Quba Mosque.",
            "announcement_type": "general",
            "priority": "important",
            "status": "published",
            "start_date": str(today),
            "end_date": str(next_week),
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["mosque"], self.mosque_quba.id)

        # Check Public City Notice Board (Must NOT appear)
        self.client.logout()
        city_pub_res = self.client.get(f"{self.public_announcements_url}?city_id={self.city_nanded.id}")
        city_items = city_pub_res.data["results"] if isinstance(city_pub_res.data, dict) and "results" in city_pub_res.data else city_pub_res.data
        city_titles = [i["title"] for i in city_items]
        self.assertNotIn("Quba Road Block", city_titles)

        # Check Mosque Public Page (MUST appear)
        mosque_pub_res = self.client.get(f"{self.public_announcements_url}?mosque_id={self.mosque_quba.id}")
        mosque_items = mosque_pub_res.data["results"] if isinstance(mosque_pub_res.data, dict) and "results" in mosque_pub_res.data else mosque_pub_res.data
        mosque_titles = [i["title"] for i in mosque_items]
        self.assertIn("Quba Road Block", mosque_titles)

    def test_city_event_created_in_city_admin_context_is_city_scoped(self):
        """Test 3: Event created in City Admin context -> Scope CITY (mosque=None) -> Appears under Nanded City Events."""
        self.client.force_authenticate(user=self.user_irshad)
        today = timezone.localdate()
        future_date = today + timezone.timedelta(days=3)

        res = self.client.post(self.city_admin_events_url, {
            "title": "Nanded Annual Conference",
            "description": "City wide conference.",
            "event_type": "lecture",
            "status": "published",
            "event_date": str(future_date),
            "event_time": "18:00:00",
            "end_time": "20:00:00",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(res.data["mosque"])

        # Public City Events check
        self.client.logout()
        pub_res = self.client.get(f"{self.public_events_url}?city_id={self.city_nanded.id}")
        items = pub_res.data["results"] if isinstance(pub_res.data, dict) and "results" in pub_res.data else pub_res.data
        titles = [i["title"] for i in items]
        self.assertIn("Nanded Annual Conference", titles)

    def test_mosque_event_created_in_my_mosque_context_does_not_leak_to_city_events(self):
        """Test 4: Event created in My Mosque context -> Scope MOSQUE (mosque=Quba) -> Appears on Quba Mosque, NOT Nanded City Events."""
        self.client.force_authenticate(user=self.user_irshad)
        today = timezone.localdate()
        future_date = today + timezone.timedelta(days=3)

        res = self.client.post(self.dashboard_events_url, {
            "title": "Quba Youth Program",
            "description": "Youth program at Quba.",
            "event_type": "youth_program",
            "status": "published",
            "event_date": str(future_date),
            "event_time": "17:00:00",
            "end_time": "19:00:00",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["mosque"], self.mosque_quba.id)

        # Check Public City Events (Must NOT appear)
        self.client.logout()
        city_res = self.client.get(f"{self.public_events_url}?city_id={self.city_nanded.id}")
        city_items = city_res.data["results"] if isinstance(city_res.data, dict) and "results" in city_res.data else city_res.data
        city_titles = [i["title"] for i in city_items]
        self.assertNotIn("Quba Youth Program", city_titles)

        # Check Mosque Public Events (MUST appear)
        mosque_res = self.client.get(f"{self.public_events_url}?mosque_id={self.mosque_quba.id}")
        mosque_items = mosque_res.data["results"] if isinstance(mosque_res.data, dict) and "results" in mosque_res.data else mosque_res.data
        mosque_titles = [i["title"] for i in mosque_items]
        self.assertIn("Quba Youth Program", mosque_titles)

    def test_mosque_content_has_no_city_admin_attribution(self):
        """Test 5: Mosque announcement/event created by dual-role user returns published_by: None and organizer_name: mosque_name."""
        self.client.force_authenticate(user=self.user_irshad)
        today = timezone.localdate()
        future_date = today + timezone.timedelta(days=3)

        ann_res = self.client.post(self.dashboard_announcements_url, {
            "title": "Quba Internal Notice",
            "content": "Notice content.",
            "announcement_type": "general",
            "priority": "normal",
            "status": "published",
            "start_date": str(today),
            "end_date": str(future_date),
        }, format="json")
        self.assertIsNone(ann_res.data["published_by"])

        evt_res = self.client.post(self.dashboard_events_url, {
            "title": "Quba Weekly Dars",
            "description": "Dars event.",
            "event_type": "dars",
            "status": "published",
            "event_date": str(future_date),
            "event_time": "18:00:00",
        }, format="json")
        self.assertIsNone(evt_res.data["published_by"])
        self.assertEqual(evt_res.data["organizer_name"], "Masjide Quba")

    def test_cross_mosque_protection(self):
        """Test 6: Mosque Admin cannot create or modify content for another mosque."""
        self.client.force_authenticate(user=self.user_irshad)
        today = timezone.localdate()
        future_date = today + timezone.timedelta(days=3)

        # Attempt to create announcement specifying Aqsa Mosque (which belongs to Hyderabad)
        res = self.client.post(self.dashboard_announcements_url, {
            "title": "Malicious Aqsa Notice",
            "content": "Content.",
            "mosque": self.mosque_aqsa.id,
            "status": "published",
            "start_date": str(today),
            "end_date": str(future_date),
        }, format="json")
        # System overrides mosque to assigned mosque (Quba) or rejects
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["mosque"], self.mosque_quba.id)

    def test_cross_city_protection(self):
        """Test 7: City Admin cannot create content for another city."""
        self.client.force_authenticate(user=self.user_irshad)
        today = timezone.localdate()
        future_date = today + timezone.timedelta(days=3)

        res = self.client.post(self.city_admin_events_url, {
            "title": "Hyderabad Event Attempt",
            "city": self.city_hyderabad.id,
            "event_type": "lecture",
            "status": "published",
            "event_date": str(future_date),
            "event_time": "18:00:00",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Backend forces city to authenticated user's city (Nanded)
        self.assertEqual(res.data["city"], self.city_nanded.id)
