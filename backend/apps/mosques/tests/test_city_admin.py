from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone

from apps.locations.models import City
from apps.accounts.models import CityAdmin, MosqueAdmin
from apps.mosques.models import Mosque, MosqueAnnouncement, MosqueEvent


class CityAdminFlowTests(APITestCase):
    def setUp(self):
        # Create cities
        self.mumbai, _ = City.objects.get_or_create(name="Mumbai", defaults={"latitude": 19.0760, "longitude": 72.8777})
        self.pune, _ = City.objects.get_or_create(name="Pune", defaults={"latitude": 18.5204, "longitude": 73.8567})

        # Create City Admin for Mumbai
        self.city_admin_user = User.objects.create_user(username="mumbaicidadmin", password="password123")
        self.city_admin = CityAdmin.objects.create(
            user=self.city_admin_user,
            city=self.mumbai,
            mobile_number="+919876543210"
        )

        # Create City Admin for Pune
        self.pune_admin_user = User.objects.create_user(username="punecidadmin", password="password123")
        self.pune_admin = CityAdmin.objects.create(
            user=self.pune_admin_user,
            city=self.pune,
            mobile_number="+918888888888"
        )

        # Create Mosque Admin
        self.mosque_admin_user = User.objects.create_user(username="mosqueadmin", password="password123")
        self.mosque = Mosque.objects.create(
            mosque_name="Mumbai Masjid",
            city="Mumbai",
            city_relation=self.mumbai,
            latitude=19.0760,
            longitude=72.8777,
            mosque_status=Mosque.MosqueStatus.ACTIVE
        )
        self.mosque_admin = MosqueAdmin.objects.create(
            user=self.mosque_admin_user,
            mosque=self.mosque,
            mobile_number="+917777777777"
        )

        # URLs
        self.announcements_url = reverse("city-admin-announcements-list")
        self.events_url = reverse("city-admin-events-list")
        self.notification_url = reverse("city-admin-notifications-send")

    def test_city_admin_can_manage_own_city_announcements(self):
        self.client.force_authenticate(user=self.city_admin_user)

        # Create general announcement
        payload = {
            "title": "Mumbai Eid Announcement",
            "content": "Eid-ul-Fitr timings will be updated soon.",
            "announcement_type": "eid",
            "priority": "important",
            "status": "published",
            "start_date": "2026-07-01",
            "end_date": "2026-07-10"
        }
        response = self.client.post(self.announcements_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["city"], self.mumbai.id)

        # Fetch announcements
        response = self.client.get(self.announcements_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Mumbai Eid Announcement")

    def test_city_admin_isolation(self):
        # Create Mumbai announcement
        MosqueAnnouncement.objects.create(
            city=self.mumbai,
            title="Mumbai Alert",
            content="Heavy rain alert",
            announcement_type="emergency",
            start_date="2026-07-01",
            end_date="2026-07-02",
            status="published"
        )

        # Pune admin tries to list announcements
        self.client.force_authenticate(user=self.pune_admin_user)
        response = self.client.get(self.announcements_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 0)  # Should not see Mumbai announcements

    def test_city_admin_cannot_assign_to_other_city_mosque(self):
        self.client.force_authenticate(user=self.pune_admin_user)

        # Pune admin tries to assign announcement to Mumbai mosque
        payload = {
            "title": "Pune event at Mumbai Mosque",
            "content": "Invalid request",
            "mosque": self.mosque.id,
            "start_date": "2026-07-01",
            "end_date": "2026-07-02"
        }
        response = self.client.post(self.announcements_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("You can only assign announcements to mosques in your city.", response.data[0])

    def test_city_admin_can_send_notifications(self):
        self.client.force_authenticate(user=self.city_admin_user)

        payload = {
            "channel": "whatsapp",
            "recipient": "+919876543210",
            "message": "Assalamu Alaikum, Mumbai community program tonight."
        }
        response = self.client.post(self.notification_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_unauthorized_users_denied_access(self):
        # Anonymous user
        response = self.client.get(self.announcements_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Mosque Admin
        self.client.force_authenticate(user=self.mosque_admin_user)
        response = self.client.get(self.announcements_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_city_admin_dashboard_stats(self):
        self.client.force_authenticate(user=self.city_admin_user)
        url = reverse("city-admin-dashboard-stats")
        
        # Initially stats should have zeros
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["announcements"]["total"], 0)
        self.assertEqual(response.data["events"]["total"], 0)

        # Create published announcement
        today = timezone.now().date()
        from datetime import timedelta
        MosqueAnnouncement.objects.create(
            city=self.mumbai,
            title="Published Alert",
            content="Alert details",
            status="published",
            priority="normal",
            start_date=today - timedelta(days=2),
            end_date=today + timedelta(days=5)
        )
        # Create draft event (upcoming event must be strictly after today)
        MosqueEvent.objects.create(
            city=self.mumbai,
            title="Draft Seminar",
            description="Details",
            status="draft",
            event_date=today + timedelta(days=1),
            event_time="18:00:00"
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["announcements"]["total"], 1)
        self.assertEqual(response.data["announcements"]["published"], 1)
        self.assertEqual(response.data["events"]["total"], 1)
        self.assertEqual(response.data["events"]["upcoming"], 1)

    def test_notification_job_enqueued_on_publish(self):
        from apps.mosques.models import NotificationJob
        initial_count = NotificationJob.objects.count()

        # Create general published announcement
        today = timezone.now().date()
        from datetime import timedelta
        MosqueAnnouncement.objects.create(
            city=self.mumbai,
            title="Safar Timing Notice",
            content="Details about timings change",
            status="published",
            start_date=today - timedelta(days=2),
            end_date=today + timedelta(days=5)
        )

        # A notification job should be enqueued
        self.assertEqual(NotificationJob.objects.count(), initial_count + 1)
        job = NotificationJob.objects.order_by("-created_at").first()
        self.assertEqual(job.title, "Safar Timing Notice")
        self.assertEqual(job.channel, "whatsapp")
        self.assertEqual(job.status, NotificationJob.Status.SENT) # Since DummyProvider returns True
