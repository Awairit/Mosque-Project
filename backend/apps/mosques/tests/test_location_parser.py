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

    @patch("urllib.request.build_opener")
    def test_short_link_redirect_resolution(self, mock_build_opener):
        # Google Maps short links require redirect resolution before coordinates can be parsed.
        mock_response = MagicMock()
        mock_response.geturl.return_value = (
            "https://www.google.com/maps/place/Masjid/@19.157829,77.335382,17z/"
        )
        mock_opener = MagicMock()
        mock_opener.open.return_value.__enter__.return_value = mock_response
        mock_build_opener.return_value = mock_opener

        url = "https://maps.app.goo.gl/f8Xy8xxhHNa1FNBT9"
        lat, lon = extract_coordinates_from_url(url)
        self.assertEqual(lat, 19.157829)
        self.assertEqual(lon, 77.335382)
        mock_opener.open.assert_called_once()

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


class BUG005SSRFAndZeroNetworkTests(TestCase):
    """Targeted regression and security tests for BUG-005."""

    @patch("urllib.request.urlopen")
    def test_model_save_executes_zero_outbound_network_calls(self, mock_urlopen):
        """Verify model save executes zero outbound HTTP network calls (Law 11 compliance)."""
        mosque = Mosque(
            mosque_name="Zero Network Mosque",
            city="Mumbai",
            address="Test address",
            google_maps_url="https://www.google.com/maps/@19.0760,72.8777,15z",
        )
        mosque.save()

        mock_urlopen.assert_not_called()
        self.assertAlmostEqual(float(mosque.latitude), 19.0760)
        self.assertAlmostEqual(float(mosque.longitude), 72.8777)

    def test_mosque_creation_without_map_url(self):
        """Mosque creation without map URL succeeds cleanly with NULL coords."""
        mosque = Mosque.objects.create(
            mosque_name="No Map URL Mosque",
            city="Delhi",
            address="Address line 1",
            google_maps_url="",
        )
        self.assertIsNone(mosque.latitude)
        self.assertIsNone(mosque.longitude)

    def test_ssrf_vector_cloud_metadata_ip_blocked(self):
        """AWS/GCP cloud metadata IP (169.254.169.254) is blocked from geocoding."""
        ssrf_url = "http://169.254.169.254/latest/meta-data/?maps.google.com"
        lat, lon = extract_coordinates_from_url(ssrf_url)
        self.assertIsNone(lat)
        self.assertIsNone(lon)

        mosque = Mosque(
            mosque_name="SSRF Attack Mosque",
            city="Delhi",
            address="Test",
            google_maps_url=ssrf_url,
        )
        mosque.save()
        self.assertIsNone(mosque.latitude)
        self.assertIsNone(mosque.longitude)

    def test_ssrf_vector_loopback_and_internal_ips_blocked(self):
        """Loopback (127.0.0.1, localhost) and internal IPs (10.0.0.1, 192.168.1.1) are blocked."""
        test_urls = [
            "http://127.0.0.1/admin?maps.google.com",
            "http://localhost/admin?maps.google.com",
            "http://10.0.0.1/secret?maps.google.com",
            "http://192.168.1.1/router?maps.google.com",
            "file:///etc/passwd?maps.google.com",
            "gopher://127.0.0.1:70/1",
        ]
        for url in test_urls:
            lat, lon = extract_coordinates_from_url(url)
            self.assertIsNone(lat, f"SSRF URL should return None lat: {url}")
            self.assertIsNone(lon, f"SSRF URL should return None lon: {url}")

    def test_untrusted_external_domains_blocked(self):
        """Non-Google domains (e.g. attacker.com) are blocked."""
        untrusted_url = "http://attacker.com/fake?query=19.157829,77.335382&maps.google.com"
        lat, lon = extract_coordinates_from_url(untrusted_url)
        self.assertIsNone(lat)
        self.assertIsNone(lon)

    def test_valid_supported_map_url_formats(self):
        """All supported Google Maps URL formats extract correctly without network I/O."""
        valid_urls = [
            ("https://www.google.com/maps/@19.157829,77.335382,15z", 19.157829, 77.335382),
            ("https://maps.google.com/?q=19.157829,77.335382", 19.157829, 77.335382),
            ("https://www.google.com/maps/place/19.157829,77.335382", 19.157829, 77.335382),
            ("https://www.google.co.in/maps/place/Masjid/data=!3d19.157829!4d77.335382", 19.157829, 77.335382),
        ]
        for url, expected_lat, expected_lon in valid_urls:
            lat, lon = extract_coordinates_from_url(url)
            self.assertAlmostEqual(lat, expected_lat, places=5)
            self.assertAlmostEqual(lon, expected_lon, places=5)


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
