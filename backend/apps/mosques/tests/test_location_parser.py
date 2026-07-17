from unittest.mock import patch, MagicMock
from django.contrib.auth.models import User
from django.test import TestCase
from django.contrib.messages import get_messages
from django.contrib.admin.sites import AdminSite

from apps.mosques.models import Mosque, MosqueRegistrationRequest
from apps.mosques.services import extract_coordinates_from_url
from apps.mosques.admin import MosqueRegistrationRequestAdmin


class LocationParserTests(TestCase):
    def test_regex_pattern_a_at_coords(self):
        url = "https://www.google.com/maps/place/Masjid/@19.157829,77.335382,17z/data=..."
        lat, lon = extract_coordinates_from_url(url)
        self.assertEqual(lat, 19.157829)
        self.assertEqual(lon, 77.335382)

    def test_regex_pattern_b_query_params(self):
        url = "https://maps.google.com/?q=19.157829,77.335382"
        lat, lon = extract_coordinates_from_url(url)
        self.assertEqual(lat, 19.157829)
        self.assertEqual(lon, 77.335382)

        url2 = "https://maps.google.com/?query=19.157829,77.335382"
        lat2, lon2 = extract_coordinates_from_url(url2)
        self.assertEqual(lat2, 19.157829)
        self.assertEqual(lon2, 77.335382)

        url3 = "https://maps.google.com/?ll=19.157829,77.335382"
        lat3, lon3 = extract_coordinates_from_url(url3)
        self.assertEqual(lat3, 19.157829)
        self.assertEqual(lon3, 77.335382)

    def test_regex_pattern_b_url_encoded(self):
        url = "https://www.google.com/maps/search/?api=1&query=19.157829%2C77.335382"
        lat, lon = extract_coordinates_from_url(url)
        self.assertEqual(lat, 19.157829)
        self.assertEqual(lon, 77.335382)

    def test_regex_pattern_c_place_path(self):
        url = "https://www.google.com/maps/place/19.157829,77.335382"
        lat, lon = extract_coordinates_from_url(url)
        self.assertEqual(lat, 19.157829)
        self.assertEqual(lon, 77.335382)

        url2 = "https://www.google.com/maps/place/19.157829+77.335382"
        lat2, lon2 = extract_coordinates_from_url(url2)
        self.assertEqual(lat2, 19.157829)
        self.assertEqual(lon2, 77.335382)

    def test_regex_pattern_d_internal_3d_4d(self):
        url = "https://www.google.com/maps/dir//Masjid/data=!3m1!4b1!4m9!4m8!1m1!4e2!1m5!1m1!1s0x3bc1e3fa29aaaaab:0x88f28c0b5aaaaaaa!2d77.335382!3d19.157829"
        # Wait, the regex expects "!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)"
        # Let's test standard "!3d19.157829!4d77.335382"
        url = "https://www.google.com/maps/dir//data=!3m1!4e2!1m5!1m1!1s0x3bc1e3f!3d19.157829!4d77.335382"
        lat, lon = extract_coordinates_from_url(url)
        self.assertEqual(lat, 19.157829)
        self.assertEqual(lon, 77.335382)

    @patch("urllib.request.urlopen")
    def test_short_link_redirect_resolution(self, mock_urlopen):
        # Mock the redirection response
        mock_response = MagicMock()
        mock_response.geturl.return_value = "https://www.google.com/maps/place/Masjid/@19.157829,77.335382,17z/"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        url = "https://maps.app.goo.gl/f8Xy8xxhHNa1FNBT9"
        lat, lon = extract_coordinates_from_url(url)
        self.assertEqual(lat, 19.157829)
        self.assertEqual(lon, 77.335382)
        mock_urlopen.assert_called_once()

    def test_invalid_urls(self):
        self.assertEqual(extract_coordinates_from_url(""), (None, None))
        self.assertEqual(extract_coordinates_from_url("not-a-url"), (None, None))
        self.assertEqual(extract_coordinates_from_url("https://google.com"), (None, None))

    def test_mosque_model_save_auto_extracts(self):
        # Create a mosque with google_maps_url but NULL coordinates
        mosque = Mosque(
            mosque_name="Save Test Mosque",
            city="Pune",
            address="Some address",
            google_maps_url="https://maps.google.com/?q=18.5204,73.8567",
        )
        # Should populate coordinates on save
        mosque.save()
        self.assertIsNotNone(mosque.latitude)
        self.assertIsNotNone(mosque.longitude)
        self.assertAlmostEqual(float(mosque.latitude), 18.5204)
        self.assertAlmostEqual(float(mosque.longitude), 73.8567)

    def test_mosque_model_save_keeps_existing_coords(self):
        # Create a mosque with both coordinates and google_maps_url
        mosque = Mosque(
            mosque_name="Keep Coords Mosque",
            city="Pune",
            address="Some address",
            latitude=12.3456,
            longitude=65.4321,
            google_maps_url="https://maps.google.com/?q=18.5204,73.8567",
        )
        mosque.save()
        # Coordinates should not be overwritten because they were already set
        self.assertAlmostEqual(float(mosque.latitude), 12.3456)
        self.assertAlmostEqual(float(mosque.longitude), 65.4321)

    @patch("apps.mosques.services.extract_coordinates_from_url")
    def test_admin_approval_workflow_warning(self, mock_extract):
        # Mock coordinate extraction to return failure
        mock_extract.return_value = (None, None)

        request = MosqueRegistrationRequest.objects.create(
            mosque_name="Warn Mosque",
            mobile_number="1234567890",
            city="Pune",
            address="Address here",
            google_maps_link="https://maps.google.com/invalid-link",
            status=MosqueRegistrationRequest.Status.PENDING,
        )

        site = AdminSite()
        admin_instance = MosqueRegistrationRequestAdmin(MosqueRegistrationRequest, site)
        admin_instance.message_user = MagicMock()

        # Mock requests for action
        mock_request = MagicMock()
        
        # Approve the request
        queryset = MosqueRegistrationRequest.objects.filter(id=request.id)
        admin_instance.approve_selected_requests(mock_request, queryset)

        # Verify mosque is created anyway
        mosque = Mosque.objects.filter(mosque_name="Warn Mosque").first()
        self.assertIsNotNone(mosque)
        self.assertIsNone(mosque.latitude)
        self.assertIsNone(mosque.longitude)

        # Verify warning message was logged
        admin_instance.message_user.assert_any_call(
            mock_request,
            "Warning: Could not extract coordinates from URL for 'Warn Mosque'. Please verify the URL or enter coordinates manually.",
            level="warning"
        )
