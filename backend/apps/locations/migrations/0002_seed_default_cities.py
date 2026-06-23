from django.db import migrations


def seed_cities(apps, schema_editor):
    City = apps.get_model("locations", "City")
    CityPrayerTiming = apps.get_model("locations", "CityPrayerTiming")

    # 1. Seed Nanded
    nanded, _ = City.objects.get_or_create(
        name="Nanded",
        defaults={"latitude": 19.138300, "longitude": 77.321000},
    )
    CityPrayerTiming.objects.get_or_create(
        city=nanded,
        calendar_date=None,
        defaults={
            "fajr_time": "04:32:00",
            "dhuhr_time": "13:18:00",
            "asr_time": "17:41:00",
            "maghrib_time": "18:58:00",
            "isha_time": "20:17:00",
        },
    )

    # 2. Seed Pune
    pune, _ = City.objects.get_or_create(
        name="Pune",
        defaults={"latitude": 18.520400, "longitude": 73.856700},
    )
    CityPrayerTiming.objects.get_or_create(
        city=pune,
        calendar_date=None,
        defaults={
            "fajr_time": "04:28:00",
            "dhuhr_time": "13:14:00",
            "asr_time": "17:37:00",
            "maghrib_time": "18:54:00",
            "isha_time": "20:11:00",
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("locations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_cities),
    ]
