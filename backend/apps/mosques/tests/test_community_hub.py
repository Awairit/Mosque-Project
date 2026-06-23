import datetime
from io import BytesIO
from PIL import Image
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import MosqueAdmin
from apps.mosques.models import Mosque, MosquePhoto, MosqueAnnouncement, MosqueEvent


def generate_mock_image(name="test.jpg"):
    file_obj = BytesIO()
    image = Image.new("RGB", (10, 10), color="red")
    image.save(file_obj, "jpeg")
    file_obj.seek(0)
    return SimpleUploadedFile(
        name=name,
        content=file_obj.read(),
        content_type="image/jpeg"
    )


class CommunityHubBackendTests(APITestCase):
    def setUp(self):
        # Create users
        self.user_a = User.objects.create_user(username="admin_a", password="password")
        self.user_b = User.objects.create_user(username="admin_b", password="password")

        # Create mosques
        self.mosque_a = Mosque.objects.create(
            mosque_name="Mosque A",
            city="Pune",
            address=" Pune Road",
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        self.mosque_b = Mosque.objects.create(
            mosque_name="Mosque B",
            city="Pune",
            address="Pune Chowk",
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

        # Link profiles
        self.admin_profile_a = MosqueAdmin.objects.create(
            user=self.user_a,
            mosque=self.mosque_a,
            mobile_number="1234567890",
            is_active=True,
        )
        self.admin_profile_b = MosqueAdmin.objects.create(
            user=self.user_b,
            mosque=self.mosque_b,
            mobile_number="9876543210",
            is_active=True,
        )

    def login_admin(self, user):
        # DRF Token authentication or force authenticate
        self.client.force_authenticate(user=user)

    def test_photo_upload_and_visibility(self):
        self.login_admin(self.user_a)

        # Create mock image file
        mock_image = generate_mock_image("test_entry.jpg")

        # Upload photo through dashboard API
        response = self.client.post(
            "/api/v1/dashboard/photos/",
            {
                "image": mock_image,
                "title": "Main Hall A",
                "caption": "Beautiful interior A",
                "display_order": 1,
                "is_active": True,
            },
            format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MosquePhoto.objects.count(), 1)
        photo = MosquePhoto.objects.first()
        self.assertEqual(photo.mosque, self.mosque_a)
        self.assertEqual(photo.uploaded_by, self.user_a)

        # Public detail view should include the photo
        self.client.force_authenticate(user=None)
        detail_response = self.client.get(f"/api/v1/mosques/{self.mosque_a.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(detail_response.data["photos"]), 1)
        self.assertEqual(detail_response.data["photos"][0]["title"], "Main Hall A")

        # Inactive photos should be hidden from public detail
        photo.is_active = False
        photo.save()
        detail_response = self.client.get(f"/api/v1/mosques/{self.mosque_a.id}/")
        self.assertEqual(len(detail_response.data["photos"]), 0)

    def test_announcement_creation_and_expiry(self):
        self.login_admin(self.user_a)

        today = timezone.localdate()

        # Create active announcement
        response = self.client.post(
            "/api/v1/dashboard/announcements/",
            {
                "title": "Water Notice",
                "content": "Maintenance today",
                "priority": "urgent",
                "status": "published",
                "start_date": today,
                "end_date": today + datetime.timedelta(days=1),
                "is_active": True,
            }
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MosqueAnnouncement.objects.count(), 1)

        # Create draft announcement (should be hidden from public)
        self.client.post(
            "/api/v1/dashboard/announcements/",
            {
                "title": "Draft Notice",
                "content": "Not published",
                "priority": "normal",
                "status": "draft",
                "start_date": today,
                "end_date": today + datetime.timedelta(days=1),
                "is_active": True,
            }
        )

        # Public detail view check
        self.client.force_authenticate(user=None)
        detail_response = self.client.get(f"/api/v1/mosques/{self.mosque_a.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        # Only the published one should appear
        self.assertEqual(len(detail_response.data["announcements"]), 1)
        self.assertEqual(detail_response.data["announcements"][0]["title"], "Water Notice")

        # Expiry test: shift dates to yesterday (expired)
        announcement = MosqueAnnouncement.objects.get(title="Water Notice")
        announcement.start_date = today - datetime.timedelta(days=2)
        announcement.end_date = today - datetime.timedelta(days=1)
        announcement.save()

        detail_response = self.client.get(f"/api/v1/mosques/{self.mosque_a.id}/")
        # Should be automatically hidden because it is expired
        self.assertEqual(len(detail_response.data["announcements"]), 0)

    def test_event_creation_and_sorting(self):
        self.login_admin(self.user_a)

        today = timezone.localdate()

        # Event A: Today (nearest)
        self.client.post(
            "/api/v1/dashboard/events/",
            {
                "title": "Weekly Dars",
                "description": "Topic: Hadith",
                "event_type": "dars",
                "status": "published",
                "event_date": today,
                "event_time": "18:00:00",
                "event_location": "Main Hall",
                "speaker_name": "Scholar A",
                "is_active": True,
            }
        )

        # Event B: Tomorrow (further)
        self.client.post(
            "/api/v1/dashboard/events/",
            {
                "title": "Youth Seminar",
                "description": "Topic: Identity",
                "event_type": "youth_program",
                "status": "published",
                "event_date": today + datetime.timedelta(days=1),
                "event_time": "10:00:00",
                "event_location": "Seminar Room",
                "speaker_name": "Speaker B",
                "is_active": True,
            }
        )

        # Public detail view check
        self.client.force_authenticate(user=None)
        detail_response = self.client.get(f"/api/v1/mosques/{self.mosque_a.id}/")
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        events = detail_response.data["events"]
        self.assertEqual(len(events), 2)
        # Sorted by nearest upcoming: Weekly Dars (today) first, Youth Seminar (tomorrow) second
        self.assertEqual(events[0]["title"], "Weekly Dars")
        self.assertEqual(events[1]["title"], "Youth Seminar")

        # Expiry test: shift Event A to yesterday (past event)
        event_a = MosqueEvent.objects.get(title="Weekly Dars")
        event_a.event_date = today - datetime.timedelta(days=1)
        event_a.save()

        detail_response = self.client.get(f"/api/v1/mosques/{self.mosque_a.id}/")
        # Event A should be automatically hidden because it's in the past
        self.assertEqual(len(detail_response.data["events"]), 1)
        self.assertEqual(detail_response.data["events"][0]["title"], "Youth Seminar")

    def test_permissions_and_cross_mosque_isolation(self):
        # 1. Anonymous users cannot access dashboard APIs
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/dashboard/photos/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Login as Admin A
        self.login_admin(self.user_a)

        # Admin A uploads a photo for Mosque A
        mock_image = generate_mock_image("mosque_a.jpg")
        response_photo = self.client.post(
            "/api/v1/dashboard/photos/",
            {
                "image": mock_image,
                "title": "Photo Mosque A",
                "display_order": 1,
            },
            format="multipart"
        )
        self.assertEqual(response_photo.status_code, status.HTTP_201_CREATED)
        photo_a_id = response_photo.data["id"]

        # 3. Login as Admin B
        self.login_admin(self.user_b)

        # Admin B tries to list photos -> should NOT see Admin A's photo
        response = self.client.get("/api/v1/dashboard/photos/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Admin B tries to retrieve Admin A's photo -> should get 404
        response = self.client.get(f"/api/v1/dashboard/photos/{photo_a_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Admin B tries to delete Admin A's photo -> should get 404
        response = self.client.delete(f"/api/v1/dashboard/photos/{photo_a_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Admin B tries to create photo forcing mosque field to Mosque A (wait, it should force it to Mosque B instead)
        mock_image_b = generate_mock_image("mosque_b.jpg")
        response_force = self.client.post(
            "/api/v1/dashboard/photos/",
            {
                "image": mock_image_b,
                "title": "Force Photo A",
                "mosque": self.mosque_a.id,  # Try to hijack to Mosque A
            },
            format="multipart"
        )
        # Creation should succeed, but model must be created under Mosque B!
        self.assertEqual(response_force.status_code, status.HTTP_201_CREATED)
        created_photo_id = response_force.data["id"]
        created_photo = MosquePhoto.objects.get(id=created_photo_id)
        self.assertEqual(created_photo.mosque, self.mosque_b)  # Hijack prevented!
