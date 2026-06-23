"""Geolocation utility functions for distance and spatial calculations."""

import math


def calculate_haversine(lat1, lon1, lat2, lon2) -> float:
    """Calculate the great-circle distance between two points in meters.

    Uses the Haversine formula.
    """
    # Convert latitude and longitude to radians
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))

    # Haversine calculation
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Earth's radius is approximately 6,371,000 meters
    return 6371000 * c
