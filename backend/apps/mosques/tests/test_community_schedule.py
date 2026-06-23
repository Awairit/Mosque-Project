import datetime
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import MosqueAdmin
from apps.mosques.models import Mosque, CommunitySchedule


class CommunityScheduleBackendTests(APITestCase):
    def setUp(self):
        # Create users
        self.user_a = User.objects.create_user(username="admin_a", password="password")
        self.user_b = User.objects.create_user(username="admin_b", password="password")

        # Create mosques
        self.mosque_a = Mosque.objects.create(
            mosque_name="Mosque A",
            city="Pune",
            address="Pune Road",
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
        self.client.force_authenticate(user=user)

    def test_create_weekly_dars(self):
        self.login_admin(self.user_a)
        today = timezone.localdate()

        response = self.client.post(
            "/api/v1/dashboard/schedules/",
            {
                "schedule_type": "weekly_dars",
                "event_date": today,
                "start_time": "18:30:00",
                "speaker": "Scholar A",
                "topic": "Seerah of Prophet",
                "extended_data": {"day_of_week": 1, "language": "English"},
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CommunitySchedule.objects.count(), 1)
        schedule = CommunitySchedule.objects.first()
        self.assertEqual(schedule.mosque, self.mosque_a)
        self.assertEqual(schedule.schedule_type, "weekly_dars")

    def test_create_khutbah_shift_and_uniqueness(self):
        self.login_admin(self.user_a)
        friday = timezone.localdate() + datetime.timedelta(days=(4 - timezone.localdate().weekday()) % 7)

        # Create Shift 1
        response1 = self.client.post(
            "/api/v1/dashboard/schedules/",
            {
                "schedule_type": "khutbah",
                "event_date": friday,
                "start_time": "12:45:00",
                "speaker": "Imam A",
                "topic": "Friday Sermon 1",
                "extended_data": {"language": "Arabic/English", "shift_number": 1},
            },
            format="json"
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Attempt to create duplicate Shift 1 (should fail validation)
        response2 = self.client.post(
            "/api/v1/dashboard/schedules/",
            {
                "schedule_type": "khutbah",
                "event_date": friday,
                "start_time": "13:30:00",
                "speaker": "Imam B",
                "topic": "Friday Sermon 2",
                "extended_data": {"language": "Arabic/English", "shift_number": 1},
            },
            format="json"
        )
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        # Shift 1 on same Friday is duplicated, validation error expected
        self.assertIn("non_field_errors", response2.data)

        # Create Shift 2 (should succeed)
        response3 = self.client.post(
            "/api/v1/dashboard/schedules/",
            {
                "schedule_type": "khutbah",
                "event_date": friday,
                "start_time": "13:30:00",
                "speaker": "Imam B",
                "topic": "Friday Sermon 2",
                "extended_data": {"language": "Arabic/English", "shift_number": 2},
            },
            format="json"
        )
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CommunitySchedule.objects.count(), 2)

    def test_permissions_and_cross_mosque_isolation(self):
        # 1. Anonymous users cannot access dashboard APIs
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/v1/dashboard/schedules/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Login as Admin A
        self.login_admin(self.user_a)
        today = timezone.localdate()

        response_create = self.client.post(
            "/api/v1/dashboard/schedules/",
            {
                "schedule_type": "weekly_dars",
                "event_date": today,
                "start_time": "18:00:00",
                "speaker": "Speaker A",
                "topic": "Hadith class",
                "extended_data": {"day_of_week": 2},
            },
            format="json"
        )
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)
        sched_a_id = response_create.data["id"]

        # 3. Login as Admin B
        self.login_admin(self.user_b)

        # Admin B tries to list schedules -> should NOT see Admin A's schedule
        response = self.client.get("/api/v1/dashboard/schedules/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

        # Admin B tries to retrieve Admin A's schedule -> should get 404
        response = self.client.get(f"/api/v1/dashboard/schedules/{sched_a_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Admin B tries to delete Admin A's schedule -> should get 404
        response = self.client.delete(f"/api/v1/dashboard/schedules/{sched_a_id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Admin B tries to hijack to Mosque A during creation -> should be forced to Mosque B
        response_hijack = self.client.post(
            "/api/v1/dashboard/schedules/",
            {
                "schedule_type": "weekly_dars",
                "event_date": today,
                "start_time": "18:00:00",
                "speaker": "Speaker B",
                "topic": "Another topic",
                "mosque": self.mosque_a.id,
                "extended_data": {"day_of_week": 3},
            },
            format="json"
        )
        self.assertEqual(response_hijack.status_code, status.HTTP_201_CREATED)
        created_sched_id = response_hijack.data["id"]
        created_sched = CommunitySchedule.objects.get(id=created_sched_id)
        self.assertEqual(created_sched.mosque, self.mosque_b)

    def test_public_visibility(self):
        # Create schedules for Mosque A
        today = timezone.localdate()
        self.login_admin(self.user_a)

        self.client.post(
            "/api/v1/dashboard/schedules/",
            {
                "schedule_type": "weekly_dars",
                "event_date": today,
                "start_time": "19:00:00",
                "speaker": "Public Speaker",
                "topic": "Public topic",
                "extended_data": {},
            },
            format="json"
        )

        # Fetch public detail view for Mosque A as anonymous
        self.client.force_authenticate(user=None)
        response = self.client.get(f"/api/v1/mosques/{self.mosque_a.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("schedules", response.data)
        self.assertEqual(len(response.data["schedules"]), 1)
        self.assertEqual(response.data["schedules"][0]["speaker"], "Public Speaker")
