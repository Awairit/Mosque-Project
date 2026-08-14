"""Unit tests verifying City Admin publisher attribution on public City Notices & City Events."""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import CityAdmin, MosqueAdmin
from apps.locations.models import City
from apps.mosques.models import Mosque, MosqueAnnouncement, MosqueEvent


class CityAdminAttributionTests(APITestCase):
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

        # Clear pre-existing CityAdmins for test cities
        CityAdmin.objects.filter(city__in=[self.city_nanded, self.city_hyderabad]).delete()

        # Create City Admin for Nanded (Mohammad Irshad)
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

        # Create Mosque Admin for Quba
        self.user_mosque_admin = User.objects.create_user(
            username="+919000000099",
            password="Password123!",
            first_name="Usman",
            last_name="Gani",
        )
        self.mosque_admin = MosqueAdmin.objects.create(
            user=self.user_mosque_admin,
            mosque=self.mosque_quba,
            mobile_number="+919000000099",
            is_active=True,
        )

        self.public_announcements_url = reverse("public-announcements-list")
        self.public_events_url = reverse("public-events-list")
        self.city_admin_announcements_url = reverse("city-admin-announcements-list")
        self.city_admin_events_url = reverse("city-admin-events-list")

    def test_city_notice_attribution_derived_automatically(self):
        """City Admin creates notice -> Public API includes published_by attribution."""
        self.client.force_authenticate(user=self.user_irshad)
        today = timezone.localdate()
        next_week = today + timezone.timedelta(days=7)

        create_res = self.client.post(self.city_admin_announcements_url, {
            "title": "Hajj Form Submission Deadline",
            "content": "Last date for submitting Hajj forms is 20 August 2026.",
            "announcement_type": "general",
            "priority": "important",
            "status": "published",
            "start_date": str(today),
            "end_date": str(next_week),
        }, format="json")
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        # Fetch public announcements for Nanded
        self.client.logout()
        pub_res = self.client.get(f"{self.public_announcements_url}?city_id={self.city_nanded.id}")
        self.assertEqual(pub_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(pub_res.data), 1)

        notice_data = pub_res.data[0]
        self.assertEqual(notice_data["title"], "Hajj Form Submission Deadline")
        self.assertIn("published_by", notice_data)
        self.assertIsNotNone(notice_data["published_by"])
        self.assertEqual(notice_data["published_by"]["name"], "Mohammad Irshad")
        self.assertEqual(notice_data["published_by"]["role"], "City Administrator")
        self.assertEqual(notice_data["published_by"]["city"], "Nanded")

    def test_city_event_attribution_derived_automatically(self):
        """City Admin creates event -> Public API includes published_by attribution."""
        self.client.force_authenticate(user=self.user_irshad)
        today = timezone.localdate()
        future_date = today + timezone.timedelta(days=2)

        create_res = self.client.post(self.city_admin_events_url, {
            "title": "Eid Prayer",
            "description": "Eid prayer at Nanded Eidgah.",
            "event_type": "eid",
            "status": "published",
            "event_date": str(future_date),
            "event_time": "07:00:00",
            "event_location": "Nanded Eidgah",
        }, format="json")
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        # Fetch public events for Nanded
        self.client.logout()
        pub_res = self.client.get(f"{self.public_events_url}?city_id={self.city_nanded.id}")
        self.assertEqual(pub_res.status_code, status.HTTP_200_OK)
        events_list = pub_res.data["results"] if isinstance(pub_res.data, dict) and "results" in pub_res.data else pub_res.data
        self.assertGreaterEqual(len(events_list), 1)

        event_data = events_list[0]
        self.assertEqual(event_data["title"], "Eid Prayer")
        self.assertIn("published_by", event_data)
        self.assertIsNotNone(event_data["published_by"])
        self.assertEqual(event_data["published_by"]["name"], "Mohammad Irshad")
        self.assertEqual(event_data["published_by"]["role"], "City Administrator")
        self.assertEqual(event_data["published_by"]["city"], "Nanded")

    def test_frontend_cannot_override_published_by(self):
        """Submitting arbitrary publisher name in POST payload is ignored."""
        self.client.force_authenticate(user=self.user_irshad)
        today = timezone.localdate()
        next_week = today + timezone.timedelta(days=7)

        create_res = self.client.post(self.city_admin_announcements_url, {
            "title": "Community Update",
            "content": "Official update.",
            "announcement_type": "general",
            "priority": "normal",
            "status": "published",
            "start_date": str(today),
            "end_date": str(next_week),
            "publisher_name": "Fake Admin",
            "published_by": {"name": "Fake Admin"},
        }, format="json")
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        # Attribution is derived from authenticated City Admin Mohammad Irshad
        self.assertEqual(create_res.data["published_by"]["name"], "Mohammad Irshad")

    def test_mosque_announcement_has_no_city_admin_attribution(self):
        """Mosque-level announcement created by Mosque Admin returns published_by: None."""
        today = timezone.localdate()
        next_week = today + timezone.timedelta(days=7)

        ann = MosqueAnnouncement.objects.create(
            mosque=self.mosque_quba,
            title="Mosque Cleaning Notice",
            content="Mosque will be cleaned.",
            start_date=today,
            end_date=next_week,
            status="published",
            created_by=self.user_mosque_admin,
        )

        pub_res = self.client.get(f"{self.public_announcements_url}?mosque_id={self.mosque_quba.id}")
        self.assertEqual(pub_res.status_code, status.HTTP_200_OK)
        target = [a for a in pub_res.data if a["id"] == ann.id][0]
        self.assertIsNone(target["published_by"])

    def test_existing_notice_without_created_by_falls_back_to_city_admin(self):
        """Legacy city notice with created_by=None falls back to active CityAdmin of that city."""
        today = timezone.localdate()
        next_week = today + timezone.timedelta(days=7)

        ann = MosqueAnnouncement.objects.create(
            city=self.city_nanded,
            title="Legacy City Notice",
            content="Legacy notice content.",
            start_date=today,
            end_date=next_week,
            status="published",
            created_by=None,
        )

        pub_res = self.client.get(f"{self.public_announcements_url}?city_id={self.city_nanded.id}")
        self.assertEqual(pub_res.status_code, status.HTTP_200_OK)
        target = [a for a in pub_res.data if a["id"] == ann.id][0]
        self.assertIsNotNone(target["published_by"])
        self.assertEqual(target["published_by"]["name"], "Mohammad Irshad")
