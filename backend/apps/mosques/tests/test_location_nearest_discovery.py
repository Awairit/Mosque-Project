"""Comprehensive tests for Mosque Location Lifecycle and Nearest-Mosque Discovery."""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import MosqueAdmin
from apps.locations.models import City
from apps.mosques.models import Mosque, MosqueRegistrationRequest
from apps.mosques.services import approve_mosque_registration_request


class MosqueLocationLifecycleAndNearestDiscoveryTests(APITestCase):
    def setUp(self):
        self.city_mumbai, _ = City.objects.get_or_create(
            name="Mumbai",
            defaults={"latitude": 19.0760, "longitude": 72.8777, "timezone": "Asia/Kolkata"}
        )
        self.superuser = User.objects.create_superuser(
            username="superadmin_test", email="admin@test.com", password="password123"
        )

    def test_a_valid_mosque_coordinates_registration_and_approval(self):
        """Test A — Create/register/approve a mosque with a known location and verify coordinates."""
        self.client.force_authenticate(user=self.superuser)

        req = MosqueRegistrationRequest.objects.create(
            mosque_name="Valid Mosque A",
            admin_name="Admin A",
            mobile_number="+919876543210",
            city="Mumbai",
            city_relation=self.city_mumbai,
            address="123 Marine Drive",
            google_maps_link="https://maps.google.com/?q=18.9438,72.8232",
            status=MosqueRegistrationRequest.Status.PENDING,
        )
        # Verify coordinates extracted on request
        self.assertIsNotNone(req.latitude)
        self.assertIsNotNone(req.longitude)
        self.assertAlmostEqual(float(req.latitude), 18.9438)
        self.assertAlmostEqual(float(req.longitude), 72.8232)

        # Approve via API
        url = reverse("platform-admin-requests-approve", kwargs={"pk": req.pk})
        res = self.client.post(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        mosque = Mosque.objects.get(mosque_name="Valid Mosque A")
        self.assertIsNotNone(mosque.latitude)
        self.assertIsNotNone(mosque.longitude)
        self.assertAlmostEqual(float(mosque.latitude), 18.9438)
        self.assertAlmostEqual(float(mosque.longitude), 72.8232)

    def test_b_missing_invalid_location_does_not_generate_fake_coordinates(self):
        """Test B — Verify system does NOT generate fake coordinates (0,0 or arbitrary defaults) when missing."""
        req = MosqueRegistrationRequest.objects.create(
            mosque_name="Unresolved Mosque B",
            admin_name="Admin B",
            mobile_number="+919876543211",
            city="Mumbai",
            city_relation=self.city_mumbai,
            address="456 Unknown St",
            google_maps_link="",
        )
        self.assertIsNone(req.latitude)
        self.assertIsNone(req.longitude)

        res = approve_mosque_registration_request(req, approved_by_user=self.superuser)
        mosque = res["mosque"]
        mosque.refresh_from_db()

        # Invariant 2: Must NOT be fake coordinates like (0,0) or hardcoded fallbacks
        self.assertIsNone(mosque.latitude)
        self.assertIsNone(mosque.longitude)

    def test_c_distance_calculation_and_nearest_first_ordering(self):
        """Test C — Known user location with mosques at 1km, 3km, 8km, 15km returns A, B, C, D in order."""
        user_lat = 19.0000
        user_lon = 72.8000

        # Create 4 mosques at known increasing distances from (19.0000, 72.8000)
        mA = Mosque.objects.create(
            mosque_name="Mosque A (1km)",
            city="Mumbai",
            city_relation=self.city_mumbai,
            address="Addr A",
            latitude=19.0100,
            longitude=72.8000,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        mB = Mosque.objects.create(
            mosque_name="Mosque B (3km)",
            city="Mumbai",
            city_relation=self.city_mumbai,
            address="Addr B",
            latitude=19.0300,
            longitude=72.8000,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        mC = Mosque.objects.create(
            mosque_name="Mosque C (8km)",
            city="Mumbai",
            city_relation=self.city_mumbai,
            address="Addr C",
            latitude=19.0800,
            longitude=72.8000,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        mD = Mosque.objects.create(
            mosque_name="Mosque D (15km)",
            city="Mumbai",
            city_relation=self.city_mumbai,
            address="Addr D",
            latitude=19.1500,
            longitude=72.8000,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

        url = f"/api/v1/mosques/?lat={user_lat}&lon={user_lon}"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", [])

        returned_names = [item["mosque_name"] for item in results]
        self.assertEqual(returned_names[:4], ["Mosque A (1km)", "Mosque B (3km)", "Mosque C (8km)", "Mosque D (15km)"])

    def test_d_realistic_nearby_mosque_under_10km_included_correctly(self):
        """Test D — A mosque within ~10km appears correctly in nearest-first discovery."""
        user_lat = 19.1000
        user_lon = 72.8500

        # Nearby Mosque (6 km away)
        m_nearby = Mosque.objects.create(
            mosque_name="Nearby Local Mosque",
            city="Mumbai",
            city_relation=self.city_mumbai,
            address="Local Street",
            latitude=19.1500,
            longitude=72.8500,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

        # Far Mosque (55 km away)
        m_far = Mosque.objects.create(
            mosque_name="Far Distant Mosque",
            city="Mumbai",
            city_relation=self.city_mumbai,
            address="Distant Highway",
            latitude=19.6000,
            longitude=72.8500,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

        url = f"/api/v1/mosques/?lat={user_lat}&lon={user_lon}"
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get("results", [])

        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["mosque_name"], "Nearby Local Mosque")

    def test_e_coordinate_persistence_after_approval(self):
        """Test E — Create -> retrieve -> refresh -> retrieve again to verify coordinate persistence."""
        mosque = Mosque.objects.create(
            mosque_name="Persistent Mosque",
            city="Mumbai",
            city_relation=self.city_mumbai,
            address="Persistent Address",
            google_maps_url="https://maps.google.com/?q=19.1234,72.5678",
            latitude=19.1234,
            longitude=72.5678,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        mosque_id = mosque.id

        # 1. Retrieve
        retrieved1 = Mosque.objects.get(pk=mosque_id)
        self.assertAlmostEqual(float(retrieved1.latitude), 19.1234)
        self.assertAlmostEqual(float(retrieved1.longitude), 72.5678)

        # 2. Refresh
        retrieved1.refresh_from_db()
        self.assertAlmostEqual(float(retrieved1.latitude), 19.1234)

        # 3. Retrieve again via API
        res = self.client.get(f"/api/v1/mosques/{mosque_id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertAlmostEqual(float(res.data["latitude"]), 19.1234)
        self.assertAlmostEqual(float(res.data["longitude"]), 72.5678)

    def test_f_approval_workflow_django_admin_and_super_admin(self):
        """Test F — Verify registration approval materializes Mosque and MosqueAdmin in both paths."""
        # 1. Super Admin API Approval Path
        req1 = MosqueRegistrationRequest.objects.create(
            mosque_name="Approved via Super Admin API",
            mobile_number="+919000000001",
            city="Mumbai",
            city_relation=self.city_mumbai,
            google_maps_link="https://maps.google.com/?q=19.2000,72.8000",
            status=MosqueRegistrationRequest.Status.PENDING,
        )
        self.client.force_authenticate(user=self.superuser)
        res1 = self.client.post(reverse("platform-admin-requests-approve", kwargs={"pk": req1.pk}))
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        m1 = Mosque.objects.get(mosque_name="Approved via Super Admin API")
        self.assertIsNotNone(m1.latitude)
        admin1 = MosqueAdmin.objects.get(mosque=m1)
        self.assertEqual(admin1.mobile_number, "+919000000001")

        # 2. Django Admin Save Model Approval Path
        req2 = MosqueRegistrationRequest.objects.create(
            mosque_name="Approved via Django Admin Save",
            mobile_number="+919000000002",
            city="Mumbai",
            city_relation=self.city_mumbai,
            google_maps_link="https://maps.google.com/?q=19.3000,72.8000",
            status=MosqueRegistrationRequest.Status.PENDING,
        )
        from apps.mosques.admin import MosqueRegistrationRequestAdmin
        admin_inst = MosqueRegistrationRequestAdmin(MosqueRegistrationRequest, None)
        req2.status = MosqueRegistrationRequest.Status.APPROVED
        admin_inst.save_model(request=None, obj=req2, form=None, change=True)

        m2 = Mosque.objects.get(mosque_name="Approved via Django Admin Save")
        self.assertIsNotNone(m2.latitude)
        admin2 = MosqueAdmin.objects.get(mosque=m2)
        self.assertEqual(admin2.mobile_number, "+919000000002")
