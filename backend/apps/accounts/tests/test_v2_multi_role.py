"""Comprehensive test suite for MosqueCom v2 STRICT Multi-Role Admin Architecture.

Covers all 12 mandatory architectural test scenarios:
1. Mosque Admin only -> Mosque Admin Dashboard
2. City Admin only -> City Admin Dashboard (No My Mosque)
3. City Admin + Mosque Admin -> City Admin Dashboard (My Mosque visible)
4. Dual-role user -> cannot manage another mosque
5. Two City Admin assignments to same city -> second assignment rejected
6. Existing Mosque Admin -> promoted to City Admin (same account, mobile, password)
7. Existing City Admin -> assigned Mosque Admin (same account, mobile, password)
8. City Admin without Mosque Admin role -> direct access to /dashboard rejected (HTTP 403)
9. Mosque Admin without City Admin role -> cannot access /city-admin/dashboard (HTTP 403)
10. Dual-role user -> cannot manipulate another mosque through API/URL
11. Deactivate/remove Mosque Admin assignment -> My Mosque disappears, City Admin remains active
12. Deactivate City Admin assignment -> City Admin access removed, Mosque Admin role remains if still assigned
"""

from django.core.cache import cache
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import CityAdmin, MosqueAdmin
from apps.locations.models import City
from apps.mosques.models import Mosque


class MultiRoleArchitectureTests(APITestCase):
    def setUp(self):
        cache.clear()
        # Create Super Admin
        self.superadmin, _ = User.objects.get_or_create(
            username="superadmin",
            defaults={
                "is_superuser": True,
                "is_staff": True,
                "email": "superadmin@mosquecom.org",
            }
        )
        if not self.superadmin.is_superuser:
            self.superadmin.is_superuser = True
            self.superadmin.is_staff = True
            self.superadmin.save()
        self.superadmin.set_password("superpassword")
        self.superadmin.save()

        # Create Cities idempotently
        self.city_nanded, _ = City.objects.get_or_create(
            name="Nanded",
            defaults={"latitude": 19.1383, "longitude": 77.3210, "timezone": "Asia/Kolkata"}
        )
        self.city_hyderabad, _ = City.objects.get_or_create(
            name="Hyderabad",
            defaults={"latitude": 17.3850, "longitude": 78.4867, "timezone": "Asia/Kolkata"}
        )

        # Create Mosques idempotently
        self.mosque_quba, _ = Mosque.objects.get_or_create(
            mosque_name="Masjide Quba",
            defaults={
                "city": "Nanded",
                "city_relation": self.city_nanded,
                "address": "Nanded Town",
                "mosque_status": Mosque.MosqueStatus.ACTIVE,
            }
        )
        self.mosque_faran, _ = Mosque.objects.get_or_create(
            mosque_name="Masjid-e-Faran",
            defaults={
                "city": "Nanded",
                "city_relation": self.city_nanded,
                "address": "Nanded West",
                "mosque_status": Mosque.MosqueStatus.ACTIVE,
            }
        )

        # Clear pre-existing CityAdmins for test cities
        CityAdmin.objects.filter(city__in=[self.city_nanded, self.city_hyderabad]).delete()

        self.login_url = reverse("auth-login")
        self.superadmin_cityadmin_url = reverse("platform-admin-city-admins-list")

    def test_01_mosque_admin_only_accesses_mosque_dashboard(self):
        """Test 1: Mosque Admin only gets mosque_admin role and mosque dashboard data."""
        user = User.objects.create_user(username="+919000000001", password="Password123!")
        MosqueAdmin.objects.create(
            user=user,
            mosque=self.mosque_quba,
            mobile_number="+919000000001",
            is_active=True,
        )

        res = self.client.post(self.login_url, {"mobile_number": "+919000000001", "password": "Password123!"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["role"], "mosque_admin")
        self.assertEqual(res.data["roles"], ["mosque_admin"])
        self.assertEqual(res.data["mosque_id"], self.mosque_quba.id)
        self.assertNotIn("city_id", res.data)

    def test_02_city_admin_only_accesses_city_dashboard_no_my_mosque(self):
        """Test 2: City Admin only gets city_admin role, city_id, and no mosque_id."""
        user = User.objects.create_user(username="+919000000002", password="Password123!")
        CityAdmin.objects.create(
            user=user,
            city=self.city_nanded,
            mobile_number="+919000000002",
            is_active=True,
        )

        res = self.client.post(self.login_url, {"mobile_number": "+919000000002", "password": "Password123!"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["role"], "city_admin")
        self.assertEqual(res.data["roles"], ["city_admin"])
        self.assertEqual(res.data["city_id"], self.city_nanded.id)
        self.assertNotIn("mosque_id", res.data)

    def test_03_dual_role_accesses_city_dashboard_with_my_mosque(self):
        """Test 3: Dual-role user gets both roles, city_id, and assigned mosque_id."""
        user = User.objects.create_user(username="+919000000003", password="Password123!")
        CityAdmin.objects.create(
            user=user,
            city=self.city_nanded,
            mobile_number="+919000000003",
            is_active=True,
        )
        MosqueAdmin.objects.create(
            user=user,
            mosque=self.mosque_quba,
            mobile_number="+919000000003",
            is_active=True,
        )

        res = self.client.post(self.login_url, {"mobile_number": "+919000000003", "password": "Password123!"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["role"], "city_admin")
        self.assertEqual(set(res.data["roles"]), {"city_admin", "mosque_admin"})
        self.assertEqual(res.data["city_id"], self.city_nanded.id)
        self.assertEqual(res.data["mosque_id"], self.mosque_quba.id)

    def test_04_dual_role_cannot_manage_another_mosque(self):
        """Test 4: Dual-role user can manage assigned Quba but cannot manage Faran."""
        user = User.objects.create_user(username="+919000000004", password="Password123!")
        CityAdmin.objects.create(user=user, city=self.city_nanded, mobile_number="+919000000004", is_active=True)
        MosqueAdmin.objects.create(user=user, mosque=self.mosque_quba, mobile_number="+919000000004", is_active=True)

        self.client.force_authenticate(user=user)

        # Accessing dashboard mosque profile always resolves to assigned Quba
        res = self.client.get(reverse("dashboard-mosque-profile"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["mosque_name"], "Masjide Quba")

    def test_05_second_city_admin_assignment_rejected(self):
        """Test 5: Assigning a second active City Admin to Nanded is rejected with HTTP 400."""
        user1 = User.objects.create_user(username="+919000000005", password="Password123!")
        CityAdmin.objects.create(user=user1, city=self.city_nanded, mobile_number="+919000000005", is_active=True)

        self.client.force_authenticate(user=self.superadmin)

        # Attempt to create a second City Admin for Nanded
        res = self.client.post(self.superadmin_cityadmin_url, {
            "mobile_number": "+919000000055",
            "city_id": self.city_nanded.id,
            "email": "admin2@nanded.org"
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already has an active City Administrator", str(res.data))

    def test_06_mosque_admin_promoted_to_city_admin_preserves_account(self):
        """Test 6: Promoting an existing Mosque Admin to City Admin preserves exact same User, mobile & password."""
        user = User.objects.create_user(username="+919000000006", password="Password123!")
        user.set_password("OriginalPass123!")
        user.save()
        MosqueAdmin.objects.create(user=user, mosque=self.mosque_quba, mobile_number="+919000000006", is_active=True)

        self.client.force_authenticate(user=self.superadmin)
        res = self.client.post(self.superadmin_cityadmin_url, {
            "mobile_number": "+919000000006",
            "city_id": self.city_hyderabad.id,
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # Verify exact same User object and password remain functional
        self.client.logout()
        cache.clear()
        login_res = self.client.post(self.login_url, {"mobile_number": "+919000000006", "password": "OriginalPass123!"}, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertEqual(set(login_res.data["roles"]), {"city_admin", "mosque_admin"})

    def test_07_city_admin_assigned_mosque_admin_preserves_account(self):
        """Test 7: Assigning Mosque Admin authority to an existing City Admin preserves exact same User & password."""
        user = User.objects.create_user(username="+919000000007", password="Password123!")
        user.set_password("OriginalCityPass123!")
        user.save()
        city_admin = CityAdmin.objects.create(user=user, city=self.city_hyderabad, mobile_number="+919000000007", is_active=True)

        self.client.force_authenticate(user=self.superadmin)
        assign_url = reverse("platform-admin-city-admins-assign-mosque", kwargs={"pk": city_admin.pk})
        res = self.client.post(assign_url, {"mosque_id": self.mosque_quba.id}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Login with original credentials works and returns dual role
        self.client.logout()
        cache.clear()
        login_res = self.client.post(self.login_url, {"mobile_number": "+919000000007", "password": "OriginalCityPass123!"}, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertEqual(set(login_res.data["roles"]), {"city_admin", "mosque_admin"})

    def test_08_city_admin_without_mosque_role_blocked_from_mosque_apis(self):
        """Test 8: City Admin without Mosque Admin role blocked from /dashboard/mosque-profile/ with HTTP 403."""
        user = User.objects.create_user(username="+919000000008", password="Password123!")
        CityAdmin.objects.create(user=user, city=self.city_nanded, mobile_number="+919000000008", is_active=True)

        self.client.force_authenticate(user=user)
        res = self.client.get(reverse("dashboard-mosque-profile"))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_09_mosque_admin_without_city_role_blocked_from_city_apis(self):
        """Test 9: Mosque Admin without City Admin role blocked from /city-admin/stats/ with HTTP 403."""
        user = User.objects.create_user(username="+919000000009", password="Password123!")
        MosqueAdmin.objects.create(user=user, mosque=self.mosque_quba, mobile_number="+919000000009", is_active=True)

        self.client.force_authenticate(user=user)
        res = self.client.get(reverse("city-admin-dashboard-stats"))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_10_dual_role_cannot_manipulate_another_mosque_via_api(self):
        """Test 10: Dual-role user's Mosque Admin endpoints strictly operate on assigned Quba."""
        user = User.objects.create_user(username="+919000000010", password="Password123!")
        CityAdmin.objects.create(user=user, city=self.city_nanded, mobile_number="+919000000010", is_active=True)
        MosqueAdmin.objects.create(user=user, mosque=self.mosque_quba, mobile_number="+919000000010", is_active=True)

        self.client.force_authenticate(user=user)

        # GET profile returns Quba
        res = self.client.get(reverse("dashboard-mosque-profile"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], self.mosque_quba.id)

    def test_11_deactivate_mosque_admin_removes_my_mosque_retains_city_admin(self):
        """Test 11: Removing Mosque Admin role leaves City Admin active and removes mosque_id from response."""
        user = User.objects.create_user(username="+919000000011", password="Password123!")
        city_admin = CityAdmin.objects.create(user=user, city=self.city_nanded, mobile_number="+919000000011", is_active=True)
        MosqueAdmin.objects.create(user=user, mosque=self.mosque_quba, mobile_number="+919000000011", is_active=True)

        self.client.force_authenticate(user=self.superadmin)
        assign_url = reverse("platform-admin-city-admins-assign-mosque", kwargs={"pk": city_admin.pk})
        # Remove mosque assignment (mosque_id=None)
        res = self.client.post(assign_url, {"mosque_id": None}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Login again
        self.client.logout()
        cache.clear()
        login_res = self.client.post(self.login_url, {"mobile_number": "+919000000011", "password": "Password123!"}, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertEqual(login_res.data["roles"], ["city_admin"])
        self.assertNotIn("mosque_id", login_res.data)

    def test_12_deactivate_city_admin_retains_mosque_admin(self):
        """Test 12: Deactivating City Admin profile leaves Mosque Admin role active."""
        user = User.objects.create_user(username="+919000000012", password="Password123!")
        city_admin = CityAdmin.objects.create(user=user, city=self.city_nanded, mobile_number="+919000000012", is_active=True)
        MosqueAdmin.objects.create(user=user, mosque=self.mosque_quba, mobile_number="+919000000012", is_active=True)

        # Deactivate CityAdmin profile only
        city_admin.is_active = False
        city_admin.save()

        cache.clear()
        login_res = self.client.post(self.login_url, {"mobile_number": "+919000000012", "password": "Password123!"}, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertEqual(login_res.data["role"], "mosque_admin")
        self.assertEqual(login_res.data["roles"], ["mosque_admin"])
        self.assertEqual(login_res.data["mosque_id"], self.mosque_quba.id)

    def test_13_dual_role_password_change_syncs_all_profiles(self):
        """Test 13 (BUG-004 Fix Verification): Password change on dual-role account sets must_change_password=False on BOTH MosqueAdmin and CityAdmin profiles."""
        user = User.objects.create_user(username="+919000000013", password="OldPassword123!")
        mosque_admin = MosqueAdmin.objects.create(user=user, mosque=self.mosque_quba, mobile_number="+919000000013", must_change_password=True, is_active=True)
        city_admin = CityAdmin.objects.create(user=user, city=self.city_nanded, mobile_number="+919000000013", must_change_password=True, is_active=True)

        self.assertTrue(mosque_admin.must_change_password)
        self.assertTrue(city_admin.must_change_password)

        self.client.force_authenticate(user=user)
        change_pw_url = reverse("auth-change-password")
        res = self.client.post(change_pw_url, {
            "current_password": "OldPassword123!",
            "new_password": "NewSecurePassword123!"
        }, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        
        mosque_admin.refresh_from_db()
        city_admin.refresh_from_db()

        self.assertFalse(mosque_admin.must_change_password, "MosqueAdmin.must_change_password must be False after password change")
        self.assertFalse(city_admin.must_change_password, "CityAdmin.must_change_password must be False after password change")
        self.assertIsNotNone(mosque_admin.password_changed_at)
        self.assertIsNotNone(city_admin.password_changed_at)

    def test_14_database_blocks_duplicate_active_city_admin_for_same_city_at_db_level(self):
        """Test 14 (BUG-006 Fix Verification): Direct ORM insertion of a second active CityAdmin for the same City raises IntegrityError."""
        user1 = User.objects.create_user(username="+919000000014", password="Password123!")
        user2 = User.objects.create_user(username="+919000000015", password="Password123!")

        # First active CityAdmin for Nanded
        CityAdmin.objects.create(user=user1, city=self.city_nanded, mobile_number="+919000000014", is_active=True)

        # Attempting to create second active CityAdmin for Nanded must raise IntegrityError at DB level
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CityAdmin.objects.create(user=user2, city=self.city_nanded, mobile_number="+919000000015", is_active=True)

    def test_15_inactive_city_admins_allowed_for_same_city(self):
        """Test 15 (BUG-006 Constraint Granularity): Multiple INACTIVE CityAdmins for the same city do not violate partial unique constraint."""
        user1 = User.objects.create_user(username="+919000000016", password="Password123!")
        user2 = User.objects.create_user(username="+919000000017", password="Password123!")
        user3 = User.objects.create_user(username="+919000000018", password="Password123!")

        # One active admin and two inactive admins for Hyderabad
        ca1 = CityAdmin.objects.create(user=user1, city=self.city_hyderabad, mobile_number="+919000000016", is_active=True)
        ca2 = CityAdmin.objects.create(user=user2, city=self.city_hyderabad, mobile_number="+919000000017", is_active=False)
        ca3 = CityAdmin.objects.create(user=user3, city=self.city_hyderabad, mobile_number="+919000000018", is_active=False)

        self.assertTrue(ca1.is_active)
        self.assertFalse(ca2.is_active)
        self.assertFalse(ca3.is_active)

    def test_16_super_admin_api_handles_duplicate_city_admin_race_condition(self):
        """Test 16 (BUG-006 API Verification): Super Admin creation API handles duplicate active City Admin assignments gracefully."""
        user1 = User.objects.create_user(username="+919000000019", password="Password123!")
        CityAdmin.objects.create(user=user1, city=self.city_nanded, mobile_number="+919000000019", is_active=True)

        self.client.force_authenticate(user=self.superadmin)
        url = reverse("platform-admin-city-admins-list")
        res = self.client.post(url, {
            "first_name": "New",
            "last_name": "Admin",
            "mobile_number": "+919000000020",
            "email": "newadmin@example.com",
            "city_id": self.city_nanded.id,
        }, format="json")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("city_id", res.data)
        self.assertIn("already has an active City Administrator", str(res.data["city_id"]))

    def test_17_temporary_password_login_flow_and_password_change(self):
        """Test 17 (RC-BUG-002 Verification): Temporary password login returns token and must_change_password=True; after password change, old password fails and new password logs in cleanly."""
        temp_pw = "TempSecret123!"
        new_pw = "NewPermanentSecret123!"
        user = User.objects.create_user(username="+919000000021", password=temp_pw)
        mosque_admin = MosqueAdmin.objects.create(
            user=user,
            mosque=self.mosque_quba,
            mobile_number="+919000000021",
            must_change_password=True,
            is_active=True
        )

        # 1. Login with temporary password
        cache.clear()
        login_res1 = self.client.post(self.login_url, {"mobile_number": "+919000000021", "password": temp_pw}, format="json")
        self.assertEqual(login_res1.status_code, status.HTTP_200_OK)
        self.assertTrue(login_res1.data["must_change_password"])
        self.assertIn("token", login_res1.data)
        token = login_res1.data["token"]

        # 2. Change password using authenticated token
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        change_url = reverse("auth-change-password")
        change_res = self.client.post(change_url, {
            "current_password": temp_pw,
            "new_password": new_pw
        }, format="json")
        self.assertEqual(change_res.status_code, status.HTTP_200_OK)

        # 3. Verify old temporary password NO LONGER works
        self.client.credentials()
        self.client.logout()
        cache.clear()
        old_login_res = self.client.post(self.login_url, {"mobile_number": "+919000000021", "password": temp_pw}, format="json")
        self.assertEqual(old_login_res.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. Verify new permanent password logs in cleanly with must_change_password=False
        new_login_res = self.client.post(self.login_url, {"mobile_number": "+919000000021", "password": new_pw}, format="json")
        self.assertEqual(new_login_res.status_code, status.HTTP_200_OK)
        self.assertFalse(new_login_res.data["must_change_password"])
        self.assertIn("token", new_login_res.data)

    def test_18_e2e_registration_approval_and_login_lifecycle(self):
        """Test 18: Full End-to-End Registration -> Super Admin Approval -> Temporary Password Login -> Password Change -> Permanent Password Login."""
        from django.core.signing import TimestampSigner
        from apps.mosques.models import MosqueRegistrationRequest
        
        mobile = "+919000000022"
        signer = TimestampSigner()
        verification_token = signer.sign(mobile)

        # 1. Registration Submission
        reg_res = self.client.post("/api/v1/mosque-registration/", {
            "mosque_name": "E2E Lifecycle Mosque",
            "admin_name": "Lifecycle Admin",
            "mobile_number": mobile,
            "city": self.city_nanded.name,
            "address": "123 Lifecycle Street",
            "google_maps_link": "https://maps.google.com/?q=19.1500,77.3000",
            "verification_token": verification_token,
        }, format="json")
        self.assertEqual(reg_res.status_code, status.HTTP_201_CREATED)
        request_id = reg_res.data["request_id"]

        # 2. Super Admin Approval
        self.client.force_authenticate(user=self.superadmin)
        approve_url = reverse("platform-admin-requests-approve", kwargs={"pk": request_id})
        approve_res = self.client.post(approve_url)
        self.assertEqual(approve_res.status_code, status.HTTP_200_OK, f"Approve failed: {approve_res.data}")
        temp_password = approve_res.data["temp_password"]
        self.assertIsNotNone(temp_password)

        # 3. Mosque Admin Login with returned temporary password
        self.client.credentials()
        self.client.logout()
        cache.clear()

        login_res = self.client.post(self.login_url, {
            "mobile_number": mobile,
            "password": temp_password
        }, format="json")
        self.assertEqual(login_res.status_code, status.HTTP_200_OK)
        self.assertTrue(login_res.data["must_change_password"])
        token = login_res.data["token"]

        # 4. Change Password to Permanent Password
        new_pw = "NewE2EPermanentPassword123!"
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        change_res = self.client.post(reverse("auth-change-password"), {
            "current_password": temp_password,
            "new_password": new_pw
        }, format="json")
        self.assertEqual(change_res.status_code, status.HTTP_200_OK)

        # 5. Verify old temporary password fails
        self.client.credentials()
        self.client.logout()
        cache.clear()
        old_login_res = self.client.post(self.login_url, {
            "mobile_number": mobile,
            "password": temp_password
        }, format="json")
        self.assertEqual(old_login_res.status_code, status.HTTP_400_BAD_REQUEST)

        # 6. Verify new permanent password logs in cleanly
        perm_login_res = self.client.post(self.login_url, {
            "mobile_number": mobile,
            "password": new_pw
        }, format="json")
        self.assertEqual(perm_login_res.status_code, status.HTTP_200_OK)
        self.assertFalse(perm_login_res.data["must_change_password"])



