from django.test import TestCase, RequestFactory
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from apps.mosques.views import MosqueListAPIView


class ProductionRendererRegressionTests(TestCase):
    """Regression tests to ensure browser-like requests to API endpoints
    select JSONRenderer under production settings.
    """

    def setUp(self):
        self.factory = RequestFactory()

    def test_browser_accept_header_does_not_select_browsable_api_renderer(self):
        """Verifies that requests with browser-like Accept headers (text/html)
        select JSONRenderer instead of BrowsableAPIRenderer when configured with production renderers.
        """
        request = self.factory.get(
            "/api/v1/mosques/",
            HTTP_ACCEPT="text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        )
        view = MosqueListAPIView.as_view(renderer_classes=[JSONRenderer])
        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertNotIsInstance(response.accepted_renderer, BrowsableAPIRenderer)
        self.assertIsInstance(response.accepted_renderer, JSONRenderer)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
