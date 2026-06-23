import datetime
from zoneinfo import ZoneInfo
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import MosqueAdmin
from apps.locations.models import City
from apps.mosques.models import Mosque
from apps.community_services.models import JanazahNotice


class JanazahNoticeBackendTests(APITestCase):
    def setUp(self):
        # Create cities with timezones
        self.city_london = City.objects.create(
            name="London Test",
            latitude=51.5074,
            longitude=-0.1278,
            timezone="Europe/London"
        )
        self.city_pune = City.objects.create(
            name="Pune Test",
            latitude=18.5204,
            longitude=73.8567,
            timezone="Asia/Kolkata"
        )

        # Create users
        self.user_a = User.objects.create_user(username="admin_a", password="password")
        self.user_b = User.objects.create_user(username="admin_b", password="password")

        # Create mosques
        self.mosque_a = Mosque.objects.create(
            mosque_name="Mosque A",
            city="London",
            city_relation=self.city_london,
            address="Baker Street",
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )
        self.mosque_b = Mosque.objects.create(
            mosque_name="Mosque B",
            city="Pune",
            city_relation=self.city_pune,
            address="Pune Road",
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

    def test_model_validations(self):
        # Janazah notice must validate dates chronologically
        today = timezone.localdate()
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)

        # 1. Death date in future should fail
        notice_future_death = JanazahNotice(
            mosque=self.mosque_a,
            deceased_name="Test Deceased",
            gender="male",
            date_of_death=tomorrow,
            salah_date=today,
            salah_time=datetime.time(13, 30),
            status="draft"
        )
        with self.assertRaises(ValidationError):
            notice_future_death.full_clean()

        # 2. Salah date before death date should fail
        notice_salah_before_death = JanazahNotice(
            mosque=self.mosque_a,
            deceased_name="Test Deceased",
            gender="male",
            date_of_death=today,
            salah_date=yesterday,
            salah_time=datetime.time(13, 30),
            status="draft"
        )
        with self.assertRaises(ValidationError):
            notice_salah_before_death.full_clean()

        # 3. Burial date before salah date should fail
        notice_burial_before_salah = JanazahNotice(
            mosque=self.mosque_a,
            deceased_name="Test Deceased",
            gender="male",
            date_of_death=yesterday,
            salah_date=today,
            salah_time=datetime.time(13, 30),
            burial_date=yesterday,
            burial_time=datetime.time(15, 0),
            status="draft"
        )
        with self.assertRaises(ValidationError):
            notice_burial_before_salah.full_clean()

    def test_serializer_privacy_and_consent(self):
        # When publish_contact_info is False, contact name/phone should be stripped/None in public representation
        self.login_admin(self.user_a)
        today = timezone.localdate()

        # Create notice with contact details but consent = False
        response = self.client.post(
            "/api/v1/dashboard/janazah/",
            {
                "deceased_name": "Deceased A",
                "gender": "male",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "13:30:00",
                "family_contact_name": "Ahmad",
                "family_contact_phone": "+44 7777 777777",
                "publish_contact_info": False,
                "status": "published"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notice_id = response.data["id"]

        # Fetch as public anonymous user (must see stripped fields)
        self.client.force_authenticate(user=None)
        response_public = self.client.get(f"/api/v1/janazah/{notice_id}/")
        self.assertEqual(response_public.status_code, status.HTTP_200_OK)
        self.assertIsNone(response_public.data.get("family_contact_name"))
        self.assertIsNone(response_public.data.get("family_contact_phone"))

        # Create notice with contact details and consent = True
        self.login_admin(self.user_a)
        response2 = self.client.post(
            "/api/v1/dashboard/janazah/",
            {
                "deceased_name": "Deceased B",
                "gender": "male",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "13:30:00",
                "family_contact_name": "Ahmad",
                "family_contact_phone": "+44 7777 777777",
                "publish_contact_info": True,
                "status": "published"
            },
            format="json"
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        notice_id_2 = response2.data["id"]

        # Fetch as public anonymous user (must see original fields)
        self.client.force_authenticate(user=None)
        response_public_2 = self.client.get(f"/api/v1/janazah/{notice_id_2}/")
        self.assertEqual(response_public_2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_public_2.data.get("family_contact_name"), "Ahmad")
        self.assertEqual(response_public_2.data.get("family_contact_phone"), "+44 7777 777777")

    def test_optimistic_locking(self):
        # Create a notice
        self.login_admin(self.user_a)
        today = timezone.localdate()
        
        response = self.client.post(
            "/api/v1/dashboard/janazah/",
            {
                "deceased_name": "John Doe",
                "gender": "male",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "13:30:00",
                "status": "draft"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notice_id = response.data["id"]
        version = response.data["version"]

        # Attempt to save with incorrect/outdated version (representing concurrent modification)
        response_conflict = self.client.put(
            f"/api/v1/dashboard/janazah/{notice_id}/",
            {
                "deceased_name": "John Doe Updated",
                "gender": "male",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "13:30:00",
                "status": "draft",
                "version": version - 1 # outdated version
            },
            format="json"
        )
        self.assertEqual(response_conflict.status_code, status.HTTP_409_CONFLICT)

        # Attempt to save with correct version (should succeed and increment version)
        response_ok = self.client.put(
            f"/api/v1/dashboard/janazah/{notice_id}/",
            {
                "deceased_name": "John Doe Updated",
                "gender": "male",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "13:30:00",
                "status": "draft",
                "version": version
            },
            format="json"
        )
        self.assertEqual(response_ok.status_code, status.HTTP_200_OK)
        self.assertEqual(response_ok.data["version"], version + 1)

    def test_dashboard_multi_mosque_isolation(self):
        # Admin A creates a notice
        self.login_admin(self.user_a)
        today = timezone.localdate()

        response = self.client.post(
            "/api/v1/dashboard/janazah/",
            {
                "deceased_name": "Mosque A Deceased",
                "gender": "male",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "13:30:00",
                "status": "draft"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notice_id = response.data["id"]

        # Login as Admin B
        self.login_admin(self.user_b)

        # 1. Admin B tries to list dashboard notices (should not see Mosque A notice)
        response_list = self.client.get("/api/v1/dashboard/janazah/")
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_list.data), 0)

        # 2. Admin B tries to update Mosque A notice -> should get 404
        response_update = self.client.put(
            f"/api/v1/dashboard/janazah/{notice_id}/",
            {
                "deceased_name": "Hijacked Name",
                "gender": "male",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "13:30:00",
                "status": "draft",
                "version": 1
            },
            format="json"
        )
        self.assertEqual(response_update.status_code, status.HTTP_404_NOT_FOUND)

        # 3. Admin B tries to delete Mosque A notice -> should get 404
        response_delete = self.client.delete(f"/api/v1/dashboard/janazah/{notice_id}/")
        self.assertEqual(response_delete.status_code, status.HTTP_404_NOT_FOUND)

        # 4. Admin B tries to hijack to Mosque A on creation -> should be forced to Mosque B
        response_create = self.client.post(
            "/api/v1/dashboard/janazah/",
            {
                "deceased_name": "Mosque B Deceased",
                "gender": "female",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "14:30:00",
                "mosque": self.mosque_a.id, # Attempt hijack
                "status": "draft"
            },
            format="json"
        )
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)
        created_id = response_create.data["id"]
        created_notice = JanazahNotice.objects.get(id=created_id)
        self.assertEqual(created_notice.mosque, self.mosque_b)

    def test_public_api_filtering(self):
        # Create published notice for Mosque A
        self.login_admin(self.user_a)
        today = timezone.localdate()
        self.client.post(
            "/api/v1/dashboard/janazah/",
            {
                "deceased_name": "Published Deceased A",
                "gender": "male",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "13:30:00",
                "status": "published"
            },
            format="json"
        )

        # Create draft notice for Mosque A
        self.client.post(
            "/api/v1/dashboard/janazah/",
            {
                "deceased_name": "Draft Deceased A",
                "gender": "female",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "14:30:00",
                "status": "draft"
            },
            format="json"
        )

        # Create published notice for Mosque B
        self.login_admin(self.user_b)
        self.client.post(
            "/api/v1/dashboard/janazah/",
            {
                "deceased_name": "Published Deceased B",
                "gender": "male",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "15:00:00",
                "status": "published"
            },
            format="json"
        )

        # As public user, fetch list
        self.client.force_authenticate(user=None)
        response_list = self.client.get("/api/v1/janazah/")
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)
        # Should return ONLY published notices (2 total, draft excluded)
        self.assertEqual(response_list.data["count"], 2)
        names = [item["deceased_name"] for item in response_list.data["results"]]
        self.assertIn("Published Deceased A", names)
        self.assertIn("Published Deceased B", names)
        self.assertNotIn("Draft Deceased A", names)

        # Filter by mosque A
        response_mosque_a = self.client.get(f"/api/v1/janazah/?mosque={self.mosque_a.id}")
        self.assertEqual(response_mosque_a.status_code, status.HTTP_200_OK)
        self.assertEqual(response_mosque_a.data["count"], 1)
        self.assertEqual(response_mosque_a.data["results"][0]["deceased_name"], "Published Deceased A")

        # Filter by city (London timezone/city)
        response_city = self.client.get(f"/api/v1/janazah/?city={self.city_london.id}")
        self.assertEqual(response_city.status_code, status.HTTP_200_OK)
        self.assertEqual(response_city.data["count"], 1)
        self.assertEqual(response_city.data["results"][0]["deceased_name"], "Published Deceased A")

    def test_timezone_inheritance_and_midnight_crossing(self):
        # Verify inheriting host mosque city timezone
        # Let's say we have London (Europe/London) and Pune (Asia/Kolkata)
        self.login_admin(self.user_a)
        
        # Test Wall-Clock Rendering outputs strings, not device timezone conversions
        today = timezone.localdate()
        response = self.client.post(
            "/api/v1/dashboard/janazah/",
            {
                "deceased_name": "Timezone Test",
                "gender": "male",
                "date_of_death": today,
                "salah_date": today,
                "salah_time": "23:30:00", # Midnight crossing potential
                "status": "published"
            },
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notice_id = response.data["id"]

        # Fetch public
        self.client.force_authenticate(user=None)
        response_pub = self.client.get(f"/api/v1/janazah/{notice_id}/")
        self.assertEqual(response_pub.status_code, status.HTTP_200_OK)
        self.assertEqual(response_pub.data["salah_time"], "23:30:00")
        self.assertEqual(response_pub.data["timezone"], "Europe/London")

    def test_auto_archiving_management_command(self):
        # We manually create two notices:
        # Notice 1: Completed & buried > 24 hours ago (should be archived)
        # Notice 2: Salah completed > 48 hours ago, no burial time (should be archived)
        # Notice 3: Salah completed 5 hours ago (should remain published)
        from django.core.management import call_command
        
        today = timezone.localdate()
        yesterday_2 = today - datetime.timedelta(days=2)
        yesterday_3 = today - datetime.timedelta(days=3)

        # Notice 1
        n1 = JanazahNotice.objects.create(
            mosque=self.mosque_a,
            deceased_name="Archivable 1",
            gender="male",
            date_of_death=yesterday_3,
            salah_date=yesterday_2,
            salah_time=datetime.time(13, 30),
            burial_date=yesterday_2,
            burial_time=datetime.time(15, 0),
            status="published"
        )
        # Notice 2
        n2 = JanazahNotice.objects.create(
            mosque=self.mosque_a,
            deceased_name="Archivable 2",
            gender="male",
            date_of_death=yesterday_3,
            salah_date=yesterday_3,
            salah_time=datetime.time(10, 0),
            status="published"
        )
        # Notice 3
        n3 = JanazahNotice.objects.create(
            mosque=self.mosque_a,
            deceased_name="Active Stay",
            gender="female",
            date_of_death=today,
            salah_date=today,
            salah_time=datetime.time(13, 30),
            status="published"
        )

        # Run command
        call_command("archive_janazahs")

        n1.refresh_from_db()
        n2.refresh_from_db()
        n3.refresh_from_db()

        self.assertEqual(n1.status, "archived")
        self.assertEqual(n2.status, "archived")
        self.assertEqual(n3.status, "published")

    def test_mosque_profile_integration(self):
        # Create active published notice for Mosque A
        today = timezone.localdate()
        JanazahNotice.objects.create(
            mosque=self.mosque_a,
            deceased_name="Integration Deceased",
            gender="male",
            date_of_death=today,
            salah_date=today,
            salah_time=datetime.time(13, 30),
            status="published"
        )
        
        # Create draft notice for Mosque A (should not show on public profile)
        JanazahNotice.objects.create(
            mosque=self.mosque_a,
            deceased_name="Draft Integration Deceased",
            gender="female",
            date_of_death=today,
            salah_date=today,
            salah_time=datetime.time(14, 30),
            status="draft"
        )

        # Call public Mosque detail endpoint
        self.client.force_authenticate(user=None)
        response = self.client.get(f"/api/v1/mosques/{self.mosque_a.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertIn("janazah_notices", response.data)
        notices = response.data["janazah_notices"]
        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0]["deceased_name"], "Integration Deceased")
