"""Management command to backfill missing coordinates for existing mosques.

Usage:
    python manage.py backfill_mosque_coordinates

The command is idempotent: mosques that already have both latitude and longitude
are skipped. It is safe to run multiple times in any environment.
"""

from django.core.management.base import BaseCommand

from apps.mosques.models import Mosque
from apps.mosques.services import extract_coordinates_from_url


class Command(BaseCommand):
    help = "Backfill missing latitude/longitude for mosques that have a Google Maps URL."

    def handle(self, *args, **options):
        # Only consider mosques that are actually missing coordinates.
        candidates = Mosque.objects.filter(
            google_maps_url__isnull=False,
        ).exclude(
            google_maps_url="",
        ).filter(
            # latitude IS NULL OR longitude IS NULL
            latitude__isnull=True,
        ) | Mosque.objects.filter(
            google_maps_url__isnull=False,
        ).exclude(
            google_maps_url="",
        ).filter(
            longitude__isnull=True,
        )

        # Deduplicate (union can produce duplicates)
        candidates = candidates.distinct()

        total = candidates.count()
        self.stdout.write(f"Found {total} mosque(s) with missing coordinates.\n")

        updated = 0
        skipped = 0
        failed = []

        for mosque in candidates.iterator():
            url = mosque.google_maps_url

            if not url:
                skipped += 1
                continue

            try:
                lat, lon = extract_coordinates_from_url(url)
            except Exception as exc:
                failed.append((mosque.mosque_name, url, str(exc)))
                continue

            if lat is None or lon is None:
                failed.append(
                    (
                        mosque.mosque_name,
                        url,
                        "Coordinate extraction returned None — unsupported URL format.",
                    )
                )
                continue

            mosque.latitude = lat
            mosque.longitude = lon
            # Use update_fields to avoid triggering full save() side-effects
            # while still persisting the new coordinate values.
            mosque.save(update_fields=["latitude", "longitude"])
            updated += 1
            self.stdout.write(
                f"  ✓ {mosque.mosque_name}: ({lat}, {lon})"
            )

        # ── Summary ──────────────────────────────────────────────────
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"Updated : {updated}")
        self.stdout.write(f"Skipped : {skipped}")
        self.stdout.write(f"Failed  : {len(failed)}")

        if failed:
            self.stdout.write("\nFailed records:")
            for name, url, reason in failed:
                self.stdout.write(f"  ✗ {name}")
                self.stdout.write(f"    URL    : {url}")
                self.stdout.write(f"    Reason : {reason}")

        self.stdout.write("=" * 50 + "\n")
