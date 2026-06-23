"""API version router."""

from django.urls import include, path


urlpatterns = [
    path("v1/", include("config.api.v1.urls")),
]
