import string
from django.db import migrations

def normalize_city_name(raw_name):
    if not raw_name:
        return ""
    cleaned = " ".join(raw_name.split())
    return cleaned.strip(string.punctuation).lower()

def backfill_mosque_cities(apps, schema_editor):
    City = apps.get_model("locations", "City")
    Mosque = apps.get_model("mosques", "Mosque")
    MosqueRegistrationRequest = apps.get_model("mosques", "MosqueRegistrationRequest")

    # 1. Backfill Mosque records
    for mosque in Mosque.objects.all():
        raw_name = mosque.city
        if not raw_name or not raw_name.strip():
            continue
            
        normalized = normalize_city_name(raw_name)
        
        # Try direct match
        city_obj = City.objects.filter(name__iexact=normalized).first()
        if not city_obj:
            # Try containment match
            city_obj = City.objects.filter(name__icontains=normalized).first()
            
        if not city_obj:
            # Auto-create for approved historical mosques to prevent data loss
            city_obj = City.objects.create(
                name=raw_name.strip(),
                latitude=mosque.latitude or 0.0,
                longitude=mosque.longitude or 0.0,
                timezone="Asia/Kolkata"
            )
            
        mosque.city_relation = city_obj
        mosque.save()

    # 2. Backfill MosqueRegistrationRequest records
    for req in MosqueRegistrationRequest.objects.all():
        # Copy original CharField value to city_raw
        req.city_raw = req.city or ""
        
        if req.city:
            normalized = normalize_city_name(req.city)
            # Try matching existing verified cities only (no auto-creation for request drafts)
            city_obj = City.objects.filter(name__iexact=normalized).first()
            if not city_obj:
                city_obj = City.objects.filter(name__icontains=normalized).first()
            if city_obj:
                req.city_relation = city_obj
                
        req.save()

def reverse_backfill(apps, schema_editor):
    Mosque = apps.get_model("mosques", "Mosque")
    MosqueRegistrationRequest = apps.get_model("mosques", "MosqueRegistrationRequest")
    
    for mosque in Mosque.objects.all():
        mosque.city_relation = None
        mosque.save()
        
    for req in MosqueRegistrationRequest.objects.all():
        req.city_relation = None
        req.city_raw = ""
        req.save()

class Migration(migrations.Migration):
    dependencies = [
        ("mosques", "0009_mosque_city_relation_and_more"),
        ("locations", "0004_city_timezone"),
    ]

    operations = [
        migrations.RunPython(backfill_mosque_cities, reverse_code=reverse_backfill),
    ]
