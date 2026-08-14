"""Automated tests for City Events & Programs lifecycle, temporal status, ordering, and attribution."""

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import CityAdmin, MosqueAdmin
from apps.locations.models import City
from apps.mosques.models import Mosque, MosqueAnnouncement, MosqueEvent


class CityEventsLifecycleTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.city_nanded, _ = City.objects.get_or_create(
            name="Nanded",
            defaults={"latitude": 19.1383, "longitude": 77.3210, "timezone": "Asia/Kolkata"}
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

        CityAdmin.objects.filter(city=self.city_nanded).delete()

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

        self.public_events_url = reverse("public-events-list")
        self.city_admin_events_url = reverse("city-admin-events-list")
        self.public_announcements_url = reverse("public-announcements-list")

    def test_future_event_has_upcoming_temporal_status(self):
        """Published future event returns temporal_status = 'upcoming'."""
        today = timezone.localdate()
        future_date = today + timezone.timedelta(days=2)

        evt = MosqueEvent.objects.create(
            city=self.city_nanded,
            title="Future Program",
            description="Future event description",
            event_type="lecture",
            status="published",
            event_date=future_date,
            event_time="18:00:00",
            created_by=self.user_irshad,
        )

        self.client.force_authenticate(user=self.user_irshad)
        res = self.client.get(self.city_admin_events_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        events_list = res.data["results"] if isinstance(res.data, dict) and "results" in res.data else res.data
        target = [e for e in events_list if e["id"] == evt.id][0]
        self.assertEqual(target["temporal_status"], "upcoming")
        self.assertEqual(target["organizer_name"], "Nanded City Administration")

    def test_past_event_has_completed_temporal_status(self):
        """Published past event returns temporal_status = 'completed'."""
        today = timezone.localdate()
        past_date = today - timezone.timedelta(days=2)

        evt = MosqueEvent.objects.create(
            city=self.city_nanded,
            title="Past Lecture",
            description="Completed lecture",
            event_type="lecture",
            status="published",
            event_date=past_date,
            event_time="19:00:00",
            created_by=self.user_irshad,
        )

        self.client.force_authenticate(user=self.user_irshad)
        res = self.client.get(self.city_admin_events_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        events_list = res.data["results"] if isinstance(res.data, dict) and "results" in res.data else res.data
        target = [e for e in events_list if e["id"] == evt.id][0]
        self.assertEqual(target["temporal_status"], "completed")

    def test_past_event_does_not_appear_in_public_upcoming_events(self):
        """Public event API excludes past/completed events."""
        today = timezone.localdate()
        past_date = today - timezone.timedelta(days=2)
        future_date = today + timezone.timedelta(days=3)

        past_evt = MosqueEvent.objects.create(
            city=self.city_nanded,
            title="Past Event Siratun Nabi",
            event_type="lecture",
            status="published",
            event_date=past_date,
            event_time="19:00:00",
            created_by=self.user_irshad,
        )
        future_evt = MosqueEvent.objects.create(
            city=self.city_nanded,
            title="Testing Event",
            event_type="lecture",
            status="published",
            event_date=future_date,
            event_time="18:00:00",
            created_by=self.user_irshad,
        )

        res = self.client.get(f"{self.public_events_url}?city_id={self.city_nanded.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        events_list = res.data["results"] if isinstance(res.data, dict) and "results" in res.data else res.data
        ids = [e["id"] for e in events_list]
        self.assertIn(future_evt.id, ids)
        self.assertNotIn(past_evt.id, ids)

    def test_upcoming_events_sorted_nearest_first(self):
        """Public upcoming events are sorted ascending by start date/time (nearest first)."""
        today = timezone.localdate()
        date_near = today + timezone.timedelta(days=1)
        date_far = today + timezone.timedelta(days=5)

        far_evt = MosqueEvent.objects.create(
            city=self.city_nanded,
            title="Far Event",
            event_type="lecture",
            status="published",
            event_date=date_far,
            event_time="18:00:00",
            created_by=self.user_irshad,
        )
        near_evt = MosqueEvent.objects.create(
            city=self.city_nanded,
            title="Near Event",
            event_type="lecture",
            status="published",
            event_date=date_near,
            event_time="18:00:00",
            created_by=self.user_irshad,
        )

        res = self.client.get(f"{self.public_events_url}?city_id={self.city_nanded.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        events_list = res.data["results"] if isinstance(res.data, dict) and "results" in res.data else res.data
        event_ids = [e["id"] for e in events_list]
        self.assertEqual(event_ids[0], near_evt.id)
        self.assertEqual(event_ids[1], far_evt.id)

    def test_city_event_attribution_and_organizer_name(self):
        """City events display 'Organized by: {City} City Administration' and backend-derived publisher."""
        self.client.force_authenticate(user=self.user_irshad)
        today = timezone.localdate()
        future_date = today + timezone.timedelta(days=2)

        res = self.client.post(self.city_admin_events_url, {
            "title": "Grand Community Gathering",
            "description": "City wide event.",
            "event_type": "lecture",
            "status": "published",
            "event_date": str(future_date),
            "event_time": "18:00:00",
            "end_time": "19:30:00",
            "publisher_name": "Spoofed Name",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["organizer_name"], "Nanded City Administration")
        self.assertEqual(res.data["published_by"]["name"], "Mohammad Irshad")
        self.assertEqual(res.data["published_by"]["role"], "City Administrator")
        self.assertEqual(res.data["published_by"]["city"], "Nanded")

    def test_mosque_level_content_unaffected(self):
        """Mosque-level events return mosque name as organizer and published_by = None."""
        today = timezone.localdate()
        future_date = today + timezone.timedelta(days=2)

        user_mosque = User.objects.create_user(
            username="+919000000088",
            password="Password123!",
            first_name="Usman",
            last_name="Gani",
        )
        MosqueAdmin.objects.create(
            user=user_mosque,
            mosque=self.mosque_quba,
            mobile_number="+919000000088",
            is_active=True,
        )

        evt = MosqueEvent.objects.create(
            mosque=self.mosque_quba,
            title="Mosque Tajweed Class",
            event_type="lecture",
            status="published",
            event_date=future_date,
            event_time="19:00:00",
            created_by=user_mosque,
        )

        res = self.client.get(f"{self.public_events_url}?mosque_id={self.mosque_quba.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        events_list = res.data["results"] if isinstance(res.data, dict) and "results" in res.data else res.data
        target = [e for e in events_list if e["id"] == evt.id][0]
        self.assertEqual(target["organizer_name"], "Masjide Quba")
        self.assertIsNone(target["published_by"])
