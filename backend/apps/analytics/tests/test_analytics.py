import uuid
from datetime import timedelta
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import CityAdmin
from apps.analytics.models import AnonymousVisitor, VisitEvent
from apps.locations.models import City
from apps.mosques.models import Mosque


class VisitorAnalyticsTests(APITestCase):
    def setUp(self):
        # Super admin
        self.superadmin = User.objects.create_superuser(
            username="superadmin",
            password="superpassword123"
        )

        # Cities
        self.mumbai, _ = City.objects.get_or_create(name="Analytics Mumbai", defaults={"latitude": 19.0760, "longitude": 72.8777})
        self.pune, _ = City.objects.get_or_create(name="Analytics Pune", defaults={"latitude": 18.5204, "longitude": 73.8567})


        # City Admin for Mumbai
        self.mumbai_admin_user = User.objects.create_user(username="mumbaiadmin", password="password123")
        self.mumbai_admin = CityAdmin.objects.create(
            user=self.mumbai_admin_user,
            city=self.mumbai,
            mobile_number="+919876543210"
        )

        # Mosques
        self.mumbai_masjid = Mosque.objects.create(
            mosque_name="Mumbai Jama Masjid",
            city="Mumbai",
            city_relation=self.mumbai
        )
        self.pune_masjid = Mosque.objects.create(
            mosque_name="Pune Central Mosque",
            city="Pune",
            city_relation=self.pune
        )

        # URLs
        self.track_url = reverse("analytics-track")
        self.overview_url = reverse("analytics-overview")
        self.city_admin_url = reverse("analytics-city-admin")

    def test_anonymous_visit_tracking_first_and_subsequent_visit(self):
        # First visit (new visitor)
        payload = {
            "path": "/mosque/1",
            "city_id": self.mumbai.id,
            "mosque_id": self.mumbai_masjid.id,
            "event_type": "mosque_detail"
        }
        response = self.client.post(self.track_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_new_visitor"])
        visitor_id = response.data["visitor_id"]

        visitor = AnonymousVisitor.objects.get(id=visitor_id)
        self.assertEqual(visitor.visit_count, 1)

        # Subsequent visit (returning visitor)
        payload_2 = {
            "visitor_id": visitor_id,
            "path": "/city/mumbai",
            "city_id": self.mumbai.id,
            "event_type": "city_page"
        }
        response_2 = self.client.post(self.track_url, payload_2)
        self.assertEqual(response_2.status_code, status.HTTP_200_OK)
        self.assertFalse(response_2.data["is_new_visitor"])
        self.assertEqual(response_2.data["visitor_id"], visitor_id)

        visitor.refresh_from_db()
        self.assertEqual(visitor.visit_count, 2)
        self.assertEqual(VisitEvent.objects.filter(visitor=visitor).count(), 2)

    def test_super_admin_analytics_overview(self):
        # Create visitors and events
        v1 = AnonymousVisitor.objects.create(visit_count=1)
        v2 = AnonymousVisitor.objects.create(visit_count=3)

        VisitEvent.objects.create(visitor=v1, path="/", city=self.mumbai)
        VisitEvent.objects.create(visitor=v2, path="/city/mumbai", city=self.mumbai)
        VisitEvent.objects.create(visitor=v2, path="/mosque/1", city=self.mumbai, mosque=self.mumbai_masjid)

        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get(self.overview_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_visits"], 3)
        self.assertEqual(response.data["unique_identified_visitors"], 2)
        self.assertEqual(response.data["new_visitors"], 1)
        self.assertEqual(response.data["returning_visitors"], 1)

    def test_city_admin_analytics_isolation(self):
        v1 = AnonymousVisitor.objects.create(visit_count=1)

        # Mumbai event
        VisitEvent.objects.create(visitor=v1, path="/mosque/1", city=self.mumbai, mosque=self.mumbai_masjid)
        # Pune event
        VisitEvent.objects.create(visitor=v1, path="/mosque/2", city=self.pune, mosque=self.pune_masjid)

        # Mumbai Admin checks analytics
        self.client.force_authenticate(user=self.mumbai_admin_user)
        response = self.client.get(self.city_admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city_name"], self.mumbai.name)

        self.assertEqual(response.data["total_visits"], 1)
        self.assertEqual(len(response.data["top_mosques"]), 1)
        self.assertEqual(response.data["top_mosques"][0]["mosque_name"], "Mumbai Jama Masjid")

    def test_visitor_tracking_deduplication_and_performance(self):
        """Test BUG-010: Immediate response and short-window deduplication prevents tracking event spam."""
        payload = {
            "path": "/mosque/1",
            "city_id": self.mumbai.id,
            "mosque_id": self.mumbai_masjid.id,
            "event_type": "page_view"
        }
        res1 = self.client.post(self.track_url, payload)
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        visitor_id = res1.data["visitor_id"]

        # Immediate duplicate request with same visitor_id, path, event_type
        payload_dup = {
            "visitor_id": visitor_id,
            "path": "/mosque/1",
            "city_id": self.mumbai.id,
            "mosque_id": self.mumbai_masjid.id,
            "event_type": "page_view"
        }
        res2 = self.client.post(self.track_url, payload_dup)
        self.assertEqual(res2.status_code, status.HTTP_200_OK)

        # First event recorded, duplicate within 3s window suppressed from creating second VisitEvent row
        visitor = AnonymousVisitor.objects.get(id=visitor_id)
        self.assertEqual(VisitEvent.objects.filter(visitor=visitor).count(), 1)

