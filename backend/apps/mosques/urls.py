"""Mosque API routes."""

from django.urls import path

from apps.mosques.views import MosqueListAPIView, MosqueDetailAPIView

urlpatterns = [
    path("", MosqueListAPIView.as_view(), name="mosque-list"),
    path("<int:pk>/", MosqueDetailAPIView.as_view(), name="mosque-detail"),
]
