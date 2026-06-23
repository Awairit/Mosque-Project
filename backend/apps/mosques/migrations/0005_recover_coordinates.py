from django.db import migrations


def recover_mosque_locations(apps, schema_editor):
    Mosque = apps.get_model("mosques", "Mosque")
    MosqueRegistrationRequest = apps.get_model("mosques", "MosqueRegistrationRequest")

    # Import the coordinate extractor service dynamically
    from apps.mosques.services import extract_coordinates_from_url

    # 1. Recover URLs from approved registration requests first (to populate empty google_maps_url on Mosque)
    approved_requests = MosqueRegistrationRequest.objects.filter(status="approved")
    for req in approved_requests:
        req_url = req.google_maps_url or req.google_maps_link
        if req_url:
            # Match mosque by name and city (case-insensitive)
            mosque = Mosque.objects.filter(
                mosque_name__iexact=req.mosque_name,
                city__iexact=req.city,
            ).first()

            if mosque and not mosque.google_maps_url:
                mosque.google_maps_url = req_url
                mosque.save()

    # 2. General recovery for all existing Mosque records
    all_mosques = Mosque.objects.all()
    for mosque in all_mosques:
        if mosque.google_maps_url and (mosque.latitude is None or mosque.longitude is None):
            lat, lon = extract_coordinates_from_url(mosque.google_maps_url)
            if lat is not None and lon is not None:
                mosque.latitude = lat
                mosque.longitude = lon
                mosque.save()


class Migration(migrations.Migration):
    dependencies = [
        ("mosques", "0004_mosque_google_maps_url_and_more"),
    ]

    operations = [
        migrations.RunPython(recover_mosque_locations, reverse_code=migrations.RunPython.noop),
    ]
