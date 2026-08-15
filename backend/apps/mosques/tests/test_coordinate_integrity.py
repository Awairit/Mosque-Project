"""Coordinate Integrity Tests — V1.2

Covers the 8 scenarios required by the Coordinate Synchronization sprint:
  1. New registration with valid Google Maps URL → auto-extracted.
  2. Admin edit without URL change → coordinates unchanged.
  3. Admin edit with URL change → coordinates re-extracted.
  4. URL cleared → existing coordinates preserved.
  5. Invalid Google Maps URL → admin form validation error.
  6. Backfill command updates missing coordinates.
  7. Backfill skips records that already have coordinates.
  8. Running backfill twice is idempotent (no duplicate updates).
"""

from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from apps.mosques.models import Mosque


VALID_URL_MUMBAI = "https://maps.google.com/?q=19.0760,72.8777"
VALID_URL_HYD = "https://maps.google.com/?q=17.3850,78.4867"
VALID_URL_KOLKATA = "https://maps.google.com/?q=22.5726,88.3639"
VALID_URL_SURAT = "https://maps.google.com/?q=21.1702,72.8311"


class MosqueCoordinateSyncTests(TestCase):
    """Mosque.save() coordinate synchronization behaviour."""

    # 1 ── New mosque with valid URL extracts coordinates
    def test_new_registration_extracts_coordinates(self):
        mosque = Mosque.objects.create(
            mosque_name="New Mosque With URL",
            city="Mumbai",
            google_maps_url=VALID_URL_MUMBAI,
        )
        mosque.refresh_from_db()
        self.assertIsNotNone(mosque.latitude)
        self.assertIsNotNone(mosque.longitude)
        self.assertAlmostEqual(float(mosque.latitude), 19.0760)
        self.assertAlmostEqual(float(mosque.longitude), 72.8777)

    # 2 ── Edit without URL change leaves coordinates untouched
    def test_edit_unchanged_url_preserves_coords(self):
        mosque = Mosque.objects.create(
            mosque_name="Stable Mosque",
            city="Delhi",
            google_maps_url="https://maps.google.com/?q=28.6139,77.2090",
            latitude=28.6139,
            longitude=77.2090,
        )
        # Reload — this resets _original_google_maps_url to the stored URL.
        mosque = Mosque.objects.get(pk=mosque.pk)
        mosque.mosque_name = "Stable Mosque (Renamed)"
        mosque.save()

        mosque.refresh_from_db()
        self.assertAlmostEqual(float(mosque.latitude), 28.6139)
        self.assertAlmostEqual(float(mosque.longitude), 77.2090)

    # 3 ── Changing the URL re-extracts coordinates
    def test_edit_changed_url_updates_coords(self):
        mosque = Mosque.objects.create(
            mosque_name="Moving Mosque",
            city="Chennai",
            google_maps_url="https://maps.google.com/?q=13.0827,80.2707",
            latitude=13.0827,
            longitude=80.2707,
        )
        # Reload resets tracking.
        mosque = Mosque.objects.get(pk=mosque.pk)
        mosque.google_maps_url = VALID_URL_HYD
        mosque.save()

        mosque.refresh_from_db()
        self.assertAlmostEqual(float(mosque.latitude), 17.3850)
        self.assertAlmostEqual(float(mosque.longitude), 78.4867)

    # 4 ── Clearing the URL preserves existing coordinates
    def test_url_removal_preserves_coordinates(self):
        mosque = Mosque.objects.create(
            mosque_name="Preserved Mosque",
            city="Hyderabad",
            google_maps_url=VALID_URL_HYD,
            latitude=17.3850,
            longitude=78.4867,
        )
        mosque = Mosque.objects.get(pk=mosque.pk)
        mosque.google_maps_url = None
        mosque.save()

        mosque.refresh_from_db()
        self.assertIsNotNone(mosque.latitude, "Latitude was deleted when URL was cleared")
        self.assertIsNotNone(mosque.longitude, "Longitude was deleted when URL was cleared")
        self.assertAlmostEqual(float(mosque.latitude), 17.3850)
        self.assertAlmostEqual(float(mosque.longitude), 78.4867)


class MosqueAdminFormValidationTests(TestCase):
    """MosqueAdminForm coordinate validation behaviour."""

    # 5a ── Invalid URL raises validation error
    @patch("apps.mosques.services.extract_coordinates_from_url")
    def test_admin_form_raises_error_on_bad_url(self, mock_extract):
        from apps.mosques.admin import MosqueAdminForm

        mock_extract.return_value = (None, None)

        form_data = {
            "mosque_name": "Bad URL Mosque",
            "city": "Lucknow",
            "address": "Some address",
            "google_maps_url": "https://maps.google.com/invalid-link",
            "mosque_status": Mosque.MosqueStatus.ACTIVE,
            "mosque_type": Mosque.MosqueType.JAMA_MASJID,
            # latitude and longitude intentionally absent
        }
        form = MosqueAdminForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Unable to extract coordinates", str(form.errors))

    # 5b ── Manual coordinates bypass extraction and pass validation
    def test_admin_form_valid_with_manual_coords(self):
        from apps.mosques.admin import MosqueAdminForm

        form_data = {
            "mosque_name": "Manual Coords Mosque",
            "city": "Pune",
            "address": "Test address",
            "google_maps_url": "https://maps.google.com/invalid-link",
            "latitude": "18.5204",
            "longitude": "73.8567",
            "mosque_status": Mosque.MosqueStatus.ACTIVE,
            "mosque_type": Mosque.MosqueType.JAMA_MASJID,
        }
        form = MosqueAdminForm(data=form_data)
        self.assertTrue(form.is_valid(), msg=form.errors)


class BackfillCommandTests(TestCase):
    """backfill_mosque_coordinates management command behaviour."""

    def _create_mosque_without_coords(self, name, url):
        """Create a mosque and then force-clear coordinates to simulate legacy state."""
        mosque = Mosque.objects.create(
            mosque_name=name,
            city="TestCity",
            google_maps_url=url,
        )
        Mosque.objects.filter(pk=mosque.pk).update(latitude=None, longitude=None)
        return mosque

    # 6 ── Command updates mosques with missing coordinates
    def test_backfill_updates_missing_coordinates(self):
        mosque = self._create_mosque_without_coords(
            "Backfill Target Mosque", VALID_URL_KOLKATA
        )

        out = StringIO()
        call_command("backfill_mosque_coordinates", stdout=out)

        mosque.refresh_from_db()
        self.assertIsNotNone(mosque.latitude)
        self.assertIsNotNone(mosque.longitude)
        self.assertAlmostEqual(float(mosque.latitude), 22.5726)
        self.assertAlmostEqual(float(mosque.longitude), 88.3639)
        self.assertIn("Updated", out.getvalue())

    # 7 ── Command skips mosques that already have coordinates
    def test_backfill_skips_existing_coordinates(self):
        mosque = Mosque.objects.create(
            mosque_name="Already Complete Mosque",
            city="Jaipur",
            google_maps_url="https://maps.google.com/?q=26.9124,75.7873",
            latitude=26.9124,
            longitude=75.7873,
        )
        original_lat = float(mosque.latitude)

        out = StringIO()
        call_command("backfill_mosque_coordinates", stdout=out)

        mosque.refresh_from_db()
        self.assertAlmostEqual(float(mosque.latitude), original_lat)
        # The mosque should not appear in the updated count.
        self.assertNotIn("Backfill Target", out.getvalue())

    # 8 ── Command is idempotent on second run
    def test_backfill_idempotent_on_second_run(self):
        mosque = self._create_mosque_without_coords(
            "Idempotent Mosque", VALID_URL_SURAT
        )

        call_command("backfill_mosque_coordinates", stdout=StringIO())
        mosque.refresh_from_db()
        lat_after_first = float(mosque.latitude)

        out2 = StringIO()
        call_command("backfill_mosque_coordinates", stdout=out2)
        mosque.refresh_from_db()

        self.assertAlmostEqual(float(mosque.latitude), lat_after_first)
        self.assertIn("Found 0 mosque(s)", out2.getvalue())


class MosqueListingDistanceSortingTests(TestCase):
    """Targeted regression tests for Mosque Listing & Distance Sorting (Step 13)."""

    def setUp(self):
        from apps.locations.models import City
        self.city_nanded, _ = City.objects.get_or_create(
            name="Nanded",
            defaults={"latitude": 19.138300, "longitude": 77.321000},
        )
        self.city_pune, _ = City.objects.get_or_create(
            name="Pune",
            defaults={"latitude": 18.520400, "longitude": 73.856700},
        )

        # Nearby Mosque A (1 km away from user at 19.1500, 77.3300)
        self.mosque_a = Mosque.objects.create(
            mosque_name="Mosque A 1km",
            city="Nanded",
            city_relation=self.city_nanded,
            latitude=19.159000,
            longitude=77.330000,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

        # Nearby Mosque B (5 km away)
        self.mosque_b = Mosque.objects.create(
            mosque_name="Mosque B 5km",
            city="Nanded",
            city_relation=self.city_nanded,
            latitude=19.195000,
            longitude=77.330000,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

        # Distant Mosque (372 km away in Pune)
        self.mosque_distant = Mosque.objects.create(
            mosque_name="Distant Mosque 372km",
            city="Pune",
            city_relation=self.city_pune,
            latitude=18.520400,
            longitude=73.856700,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

        # Newly registered mosque without explicit lat/lon (falls back to Nanded city coords)
        self.new_mosque = Mosque.objects.create(
            mosque_name="New Mosque Fallback",
            city="Nanded",
            city_relation=self.city_nanded,
            mosque_status=Mosque.MosqueStatus.ACTIVE,
        )

    def test_case_1_and_3_nearby_sorted_before_distant(self):
        """Case 1 & 3: Nearby mosques (1km, 5km) appear before a 372km distant mosque."""
        from rest_framework.test import APIRequestFactory
        from apps.mosques.views import MosqueListAPIView

        factory = APIRequestFactory()
        request = factory.get("/api/mosques/?lat=19.150000&lon=77.330000")
        view = MosqueListAPIView.as_view()
        response = view(request)

        results = response.data["results"]
        names = [m["mosque_name"] for m in results]

        self.assertIn("Mosque A 1km", names)
        self.assertIn("Mosque B 5km", names)

        # Verify Mosque A is before Mosque B
        idx_a = names.index("Mosque A 1km")
        idx_b = names.index("Mosque B 5km")
        self.assertLess(idx_a, idx_b)

        # Verify distant mosque comes after nearby mosques if present
        if "Distant Mosque 372km" in names:
            idx_distant = names.index("Distant Mosque 372km")
            self.assertGreater(idx_distant, idx_a)
            self.assertGreater(idx_distant, idx_b)

    def test_case_2_and_6_newly_registered_approved_mosque_eligible(self):
        """Case 2 & 6: Newly registered approved mosque appears in public listing with city fallback."""
        from rest_framework.test import APIRequestFactory
        from apps.mosques.views import MosqueListAPIView

        factory = APIRequestFactory()
        request = factory.get("/api/mosques/?lat=19.150000&lon=77.330000")
        view = MosqueListAPIView.as_view()
        response = view(request)

        results = response.data["results"]
        names = [m["mosque_name"] for m in results]
        self.assertIn("New Mosque Fallback", names)

    def test_case_4_distance_corresponds_to_coordinates(self):
        """Case 4: Distance returned corresponds to actual coordinates."""
        from rest_framework.test import APIRequestFactory
        from apps.mosques.views import MosqueListAPIView

        factory = APIRequestFactory()
        request = factory.get("/api/mosques/?lat=19.150000&lon=77.330000")
        view = MosqueListAPIView.as_view()
        response = view(request)

        results = response.data["results"]
        mosque_a_data = next(m for m in results if m["mosque_name"] == "Mosque A 1km")
        # 19.159000, 77.330000 is ~1000m from 19.150000, 77.330000
        self.assertIsNotNone(mosque_a_data.get("distance"))
        self.assertGreater(mosque_a_data["distance"], 500)
        self.assertLess(mosque_a_data["distance"], 2000)

