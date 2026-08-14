from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.community_services.models import JanazahNotice


class Command(BaseCommand):
    help = "Auto-archive completed Janazah notices."

    def handle(self, *args, **options):
        now = timezone.now()
        active_notices = JanazahNotice.objects.select_related(
            "mosque__city_relation"
        ).filter(
            status__in=[
                JanazahNotice.StatusChoices.PUBLISHED,
                JanazahNotice.StatusChoices.COMPLETED,
            ]
        )

        to_archive_ids = []
        for notice in active_notices:
            # Determine mosque timezone
            tz_str = "UTC"
            if notice.mosque and notice.mosque.city_relation:
                tz_str = notice.mosque.city_relation.timezone
            tz = ZoneInfo(tz_str)

            # Check based on burial_date
            if notice.burial_date:
                b_time = notice.burial_time or time(23, 59, 59)
                combined_dt = datetime.combine(notice.burial_date, b_time).replace(tzinfo=tz)
                # Archive if burial occurred > 24 hours ago
                if now - combined_dt > timedelta(hours=24):
                    to_archive_ids.append(notice.id)
            else:
                # Check based on salah_date
                s_time = notice.salah_time or time(12, 0)
                combined_dt = datetime.combine(notice.salah_date, s_time).replace(tzinfo=tz)
                # Archive if salah occurred > 48 hours ago
                if now - combined_dt > timedelta(hours=48):
                    to_archive_ids.append(notice.id)

        archived_count = 0
        if to_archive_ids:
            archived_count = JanazahNotice.objects.filter(id__in=to_archive_ids).update(
                status=JanazahNotice.StatusChoices.ARCHIVED,
                archived_at=now,
            )

        self.stdout.write(self.style.SUCCESS(f"Successfully archived {archived_count} Janazah notices."))
