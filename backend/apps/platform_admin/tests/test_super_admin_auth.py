from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.locations.models import City
from apps.mosques.models import Mosque, MosqueRegistrationRequest


class SuperAdminAuthAndStatsTests(APITestCase):
    def setUp(self):
        # Create superuser
        self.super_user = User.objects.create_superuser(
            username="superadmin",
            password="superpassword",
            email="super@mosquefinder.org"
        )
        # Create normal user
        self.normal_user = User.objects.create_user(
            username="normaluser",
            password="normalpassword"
        )
        
        self.login_url = reverse("platform-admin-login")
        self.stats_url = reverse("platform-admin-stats")

    def test_super_admin_login_success(self):
        data = {
            "username": "superadmin",
            "password": "superpassword"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["username"], "superadmin")

    def test_normal_user_login_denied(self):
        data = {
            "username": "normaluser",
            "password": "normalpassword"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("non_field_errors", response.data)

    def test_login_invalid_credentials(self):
        data = {
            "username": "superadmin",
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_stats_requires_authentication(self):
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dashboard_stats_denies_normal_user(self):
        # Authenticate normal user
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.get(self.stats_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_stats_allows_superuser_with_data(self):
        # Create dummy data to verify query counts
        City.objects.create(name="London", latitude=51.5074, longitude=-0.1278)
        City.objects.create(name="Manchester", latitude=53.4808, longitude=-2.2426)
        
        MosqueRegistrationRequest.objects.create(
            mosque_name="Pending Mosque A",
            admin_name="Ahmad",
            mobile_number="1122334455",
            city="London",
            address="Street A",
            status=MosqueRegistrationRequest.Status.PENDING
        )
        
        # Approve one request
        req = MosqueRegistrationRequest.objects.create(
            mosque_name="Approved Mosque B",
            admin_name="Bilal",
            mobile_number="5544332211",
            city="Manchester",
            address="Street B",
            status=MosqueRegistrationRequest.Status.PENDING
        )
        Mosque.objects.create(
            mosque_name=req.mosque_name,
            city=req.city,
            address=req.address
        )
        req.status = MosqueRegistrationRequest.Status.APPROVED
        req.save()

        # Get expected baseline counts dynamically
        expected_pending = MosqueRegistrationRequest.objects.filter(
            status=MosqueRegistrationRequest.Status.PENDING
        ).count()
        expected_approved = Mosque.objects.count()
        expected_cities = City.objects.count()

        # Authenticate superuser
        self.client.force_authenticate(user=self.super_user)
        response = self.client.get(self.stats_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["pending_mosque_requests"], expected_pending)
        self.assertEqual(response.data["approved_mosques"], expected_approved)
        self.assertEqual(response.data["cities"], expected_cities)
        self.assertEqual(response.data["prayer_timetable_imports"], 14) # Mock count
        self.assertEqual(response.data["system_status"], "Healthy")
