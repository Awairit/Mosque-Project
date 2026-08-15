from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.locations.models import City
from apps.accounts.models import CityAdmin


class SuperAdminCityAdminManagementTests(APITestCase):
    def setUp(self):
        # Super admin user
        self.superadmin = User.objects.create_superuser(
            username="superadmin",
            password="superpassword123",
            email="superadmin@mosquecom.org"
        )

        # Regular user
        self.regular_user = User.objects.create_user(
            username="regularuser",
            password="userpassword123"
        )

        # Cities
        self.delhi = City.objects.create(
            name="Delhi",
            latitude=28.6139,
            longitude=77.2090
        )
        self.lucknow = City.objects.create(
            name="Lucknow",
            latitude=26.8467,
            longitude=80.9462
        )

        # URLs
        self.list_create_url = reverse("platform-admin-city-admins-list")

    def test_super_admin_can_list_and_create_city_admin(self):
        self.client.force_authenticate(user=self.superadmin)

        # Create City Admin
        payload = {
            "mobile_number": "+919988776655",
            "city_id": self.delhi.id,
            "email": "delhi.admin@mosquecom.org",
            "first_name": "Delhi",
            "last_name": "Admin"
        }
        response = self.client.post(self.list_create_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("temp_password", response.data)
        self.assertEqual(response.data["city_name"], "Delhi")
        self.assertTrue(response.data["must_change_password"])

        # List City Admins
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["mobile_number"], "+919988776655")

    def test_super_admin_can_update_and_deactivate_city_admin(self):
        self.client.force_authenticate(user=self.superadmin)

        # Create City Admin
        user = User.objects.create_user(username="+919988776655", password="temppassword123")
        city_admin = CityAdmin.objects.create(
            user=user,
            city=self.delhi,
            mobile_number="+919988776655",
            is_active=True
        )

        detail_url = reverse("platform-admin-city-admins-detail", kwargs={"pk": city_admin.pk})

        # Update City Admin to Lucknow
        patch_payload = {
            "city_id": self.lucknow.id,
            "first_name": "UpdatedName"
        }
        response = self.client.patch(detail_url, patch_payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["city_name"], "Lucknow")
        self.assertEqual(response.data["first_name"], "UpdatedName")

        # Deactivate City Admin
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        city_admin.refresh_from_db()
        self.assertFalse(city_admin.is_active)
        self.assertFalse(city_admin.user.is_active)

    def test_super_admin_can_reset_city_admin_password(self):
        self.client.force_authenticate(user=self.superadmin)

        user = User.objects.create_user(username="+919988776655", password="oldpassword123")
        city_admin = CityAdmin.objects.create(
            user=user,
            city=self.delhi,
            mobile_number="+919988776655",
            is_active=True
        )

        reset_url = reverse("platform-admin-city-admins-reset-password", kwargs={"pk": city_admin.pk})
        response = self.client.post(reset_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("temp_password", response.data)

        city_admin.refresh_from_db()
        self.assertTrue(city_admin.must_change_password)

    def test_non_super_admin_denied_access(self):
        # Unauthenticated
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Regular user
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.list_create_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_promote_existing_mosque_admin_to_city_admin_and_assign_mosque(self):
        from apps.mosques.models import Mosque
        from apps.accounts.models import MosqueAdmin

        self.client.force_authenticate(user=self.superadmin)

        mosque = Mosque.objects.create(
            mosque_name="Masjid Taqwa",
            address="123 Main St",
            city="Delhi",
            mosque_status="active"
        )
        mosque_user = User.objects.create_user(username="+919876543210", password="password123")
        mosque_admin = MosqueAdmin.objects.create(
            user=mosque_user,
            mosque=mosque,
            mobile_number="+919876543210",
            is_active=True
        )

        # 1. Promote existing MosqueAdmin user to CityAdmin
        payload = {
            "mobile_number": "+919876543210",
            "city_id": self.delhi.id,
            "email": "promoted@mosquecom.org"
        }
        response = self.client.post(self.list_create_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        city_admin_id = response.data["id"]

        # 2. Login as dual-role user
        login_response = self.client.post(reverse("auth-login"), {
            "mobile_number": "+919876543210",
            "password": "password123"
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("city_admin", login_response.data["roles"])
        self.assertIn("mosque_admin", login_response.data["roles"])
        self.assertEqual(login_response.data["mosque_id"], mosque.id)
        self.assertEqual(login_response.data["city_id"], self.delhi.id)

        # 3. Assign Mosque via Super Admin Assign Mosque API
        assign_url = reverse("platform-admin-city-admins-assign-mosque", kwargs={"pk": city_admin_id})
        assign_res = self.client.post(assign_url, {"mosque_id": mosque.id})
        self.assertEqual(assign_res.status_code, status.HTTP_200_OK)
        self.assertEqual(assign_res.data["city_admin"]["mosque_id"], mosque.id)
