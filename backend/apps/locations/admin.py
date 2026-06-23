"""Django admin registrations for location models."""

import os
from datetime import datetime
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction
from django.utils import timezone
from django.template.response import TemplateResponse
from django.contrib import messages

from apps.locations.models import City, CityPrayerTiming, CityDailyPrayerTiming, CityCalendarImportLog
from apps.locations.services import parse_and_validate_calendar_csv


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "timezone", "latitude", "longitude", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "import-calendar/",
                self.admin_site.admin_view(self.import_calendar_view),
                name="locations_city_import_calendar",
            ),
        ]
        return custom_urls + urls

    def download_template_view(self, request):
        # Generate sample CSV response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="city_prayer_calendar_template.csv"'
        
        writer = csv.writer(response)
        writer.writerow(["date", "fajr_time", "sunrise_time", "dhuhr_time", "asr_time", "maghrib_time", "isha_time"])
        writer.writerow(["2026-06-01", "04:30:00", "05:55:00", "12:30:00", "16:00:00", "19:05:00", "20:30:00"])
        writer.writerow(["2026-06-02", "04:30:00", "05:55:00", "12:30:00", "16:00:00", "19:05:00", "20:30:00"])
        writer.writerow(["2026-06-03", "04:31:00", "05:56:00", "12:30:00", "16:01:00", "19:06:00", "20:31:00"])
        return response

    def import_calendar_view(self, request):
        # Check download template parameter
        if request.GET.get("download_template"):
            import csv
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="city_prayer_calendar_template.csv"'
            writer = csv.writer(response)
            writer.writerow(["date", "fajr_time", "sunrise_time", "dhuhr_time", "asr_time", "maghrib_time", "isha_time"])
            writer.writerow(["2026-06-01", "04:30:00", "05:55:00", "12:30:00", "16:00:00", "19:05:00", "20:30:00"])
            writer.writerow(["2026-06-02", "04:30:00", "05:55:00", "12:30:00", "16:00:00", "19:05:00", "20:30:00"])
            writer.writerow(["2026-06-03", "04:31:00", "05:56:00", "12:30:00", "16:01:00", "19:06:00", "20:31:00"])
            return response

        context = {
            **self.admin_site.each_context(request),
            "title": "Import City Prayer Calendar",
            "opts": self.model._meta,
            "cities": City.objects.all().order_by("name"),
            "step": "upload",
        }

        # Step 1: Handle CSV Upload & Validation
        if request.method == "POST" and "validate" in request.POST:
            city_id = request.POST.get("city")
            csv_file = request.FILES.get("csv_file")

            if not city_id:
                context["error_list"] = ["Please select a city."]
                return TemplateResponse(request, "admin/locations/city/import_calendar.html", context)
            if not csv_file:
                context["error_list"] = ["Please select a CSV file."]
                return TemplateResponse(request, "admin/locations/city/import_calendar.html", context)

            city = City.objects.filter(id=city_id).first()
            if not city:
                context["error_list"] = ["Selected city does not exist."]
                return TemplateResponse(request, "admin/locations/city/import_calendar.html", context)

            # Parse and Validate the CSV file in memory
            result = parse_and_validate_calendar_csv(csv_file, city_id)
            if not result["success"]:
                context["error_list"] = result["errors"]
                return TemplateResponse(request, "admin/locations/city/import_calendar.html", context)

            # Save the file temporarily in workspace
            temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tmp_imports")
            os.makedirs(temp_dir, exist_ok=True)
            temp_filepath = os.path.join(temp_dir, f"import_{request.user.id}_{city.id}.csv")
            
            try:
                with open(temp_filepath, "wb") as f:
                    csv_file.seek(0)
                    f.write(csv_file.read())
            except Exception as e:
                context["error_list"] = [f"Failed to create temporary import file: {str(e)}"]
                return TemplateResponse(request, "admin/locations/city/import_calendar.html", context)

            # Calculate Dry-Run statistics
            rows = result["rows"]
            dates = [r["date"] for r in rows]
            existing_timings = {
                t.date.strftime("%Y-%m-%d"): t
                for t in CityDailyPrayerTiming.objects.filter(city=city, date__in=dates)
            }

            to_create_count = 0
            to_update_count = 0
            skipped_count = 0

            for r in rows:
                date_str = r["date"]
                fajr_t = datetime.strptime(r["fajr_time"], "%H:%M:%S").time()
                sunrise_t = datetime.strptime(r["sunrise_time"], "%H:%M:%S").time()
                dhuhr_t = datetime.strptime(r["dhuhr_time"], "%H:%M:%S").time()
                asr_t = datetime.strptime(r["asr_time"], "%H:%M:%S").time()
                maghrib_t = datetime.strptime(r["maghrib_time"], "%H:%M:%S").time()
                isha_t = datetime.strptime(r["isha_time"], "%H:%M:%S").time()

                if date_str not in existing_timings:
                    to_create_count += 1
                else:
                    existing = existing_timings[date_str]
                    if (
                        existing.fajr_time != fajr_t
                        or existing.sunrise_time != sunrise_t
                        or existing.dhuhr_time != dhuhr_t
                        or existing.asr_time != asr_t
                        or existing.maghrib_time != maghrib_t
                        or existing.isha_time != isha_t
                    ):
                        to_update_count += 1
                    else:
                        skipped_count += 1

            # Update context for Step 2
            context.update({
                "step": "preview",
                "city": city,
                "filename": csv_file.name,
                "temp_file": temp_filepath,
                "rows_processed": len(rows),
                "rows_created": to_create_count,
                "rows_updated": to_update_count,
                "rows_skipped": skipped_count,
                "preview": result["preview"],
            })
            return TemplateResponse(request, "admin/locations/city/import_calendar.html", context)

        # Step 2: Handle Confirmation & Transaction Commit
        elif request.method == "POST" and "commit" in request.POST:
            city_id = request.POST.get("city_id")
            temp_filepath = request.POST.get("temp_file")
            filename = request.POST.get("filename")

            if not city_id or not temp_filepath or not os.path.exists(temp_filepath):
                messages.error(request, "Import session expired or is invalid. Please start over.")
                return HttpResponseRedirect(request.path)

            city = City.objects.filter(id=city_id).first()
            if not city:
                messages.error(request, "City details could not be resolved.")
                return HttpResponseRedirect(request.path)

            # Re-parse file to retrieve rows
            with open(temp_filepath, "r", encoding="utf-8-sig") as f:
                result = parse_and_validate_calendar_csv(f.read(), city.id)

            if not result["success"]:
                messages.error(request, f"Validation checks failed on confirmation: {', '.join(result['errors'])}")
                return HttpResponseRedirect(request.path)

            rows = result["rows"]
            dates = [r["date"] for r in rows]
            
            existing_timings = {
                t.date.strftime("%Y-%m-%d"): t
                for t in CityDailyPrayerTiming.objects.filter(city=city, date__in=dates)
            }

            to_create = []
            to_update = []
            skipped = 0

            for r in rows:
                date_obj = datetime.strptime(r["date"], "%Y-%m-%d").date()
                fajr_t = datetime.strptime(r["fajr_time"], "%H:%M:%S").time()
                sunrise_t = datetime.strptime(r["sunrise_time"], "%H:%M:%S").time()
                dhuhr_t = datetime.strptime(r["dhuhr_time"], "%H:%M:%S").time()
                asr_t = datetime.strptime(r["asr_time"], "%H:%M:%S").time()
                maghrib_t = datetime.strptime(r["maghrib_time"], "%H:%M:%S").time()
                isha_t = datetime.strptime(r["isha_time"], "%H:%M:%S").time()

                if r["date"] not in existing_timings:
                    to_create.append(
                        CityDailyPrayerTiming(
                            city=city,
                            date=date_obj,
                            fajr_time=fajr_t,
                            sunrise_time=sunrise_t,
                            dhuhr_time=dhuhr_t,
                            asr_time=asr_t,
                            maghrib_time=maghrib_t,
                            isha_time=isha_t,
                        )
                    )
                else:
                    existing = existing_timings[r["date"]]
                    has_changes = (
                        existing.fajr_time != fajr_t
                        or existing.sunrise_time != sunrise_t
                        or existing.dhuhr_time != dhuhr_t
                        or existing.asr_time != asr_t
                        or existing.maghrib_time != maghrib_t
                        or existing.isha_time != isha_t
                    )

                    if has_changes:
                        existing.fajr_time = fajr_t
                        existing.sunrise_time = sunrise_t
                        existing.dhuhr_time = dhuhr_t
                        existing.asr_time = asr_t
                        existing.maghrib_time = maghrib_t
                        existing.isha_time = isha_t
                        to_update.append(existing)
                    else:
                        skipped += 1

            # Commit changes in atomic transaction
            try:
                with transaction.atomic():
                    if to_create:
                        CityDailyPrayerTiming.objects.bulk_create(to_create)
                    if to_update:
                        CityDailyPrayerTiming.objects.bulk_update(
                            to_update,
                            fields=["fajr_time", "sunrise_time", "dhuhr_time", "asr_time", "maghrib_time", "isha_time"]
                        )
                    
                    # Create import log entry
                    log = CityCalendarImportLog.objects.create(
                        city=city,
                        uploaded_by=request.user,
                        filename=filename,
                        rows_processed=len(rows),
                        rows_created=len(to_create),
                        rows_updated=len(to_update),
                        rows_skipped=skipped,
                        status="success",
                    )
            except Exception as e:
                messages.error(request, f"Database transaction commit failed: {str(e)}")
                return HttpResponseRedirect(request.path)
            finally:
                # Clean up temporary file
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)

            # Update context for Step 3
            context.update({
                "step": "completed",
                "city": city,
                "log": log,
            })
            return TemplateResponse(request, "admin/locations/city/import_calendar.html", context)

        return TemplateResponse(request, "admin/locations/city/import_calendar.html", context)


@admin.register(CityPrayerTiming)
class CityPrayerTimingAdmin(admin.ModelAdmin):
    list_display = (
        "city",
        "calendar_date",
        "fajr_time",
        "dhuhr_time",
        "asr_time",
        "maghrib_time",
        "isha_time",
    )
    list_filter = ("city", "calendar_date")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CityDailyPrayerTiming)
class CityDailyPrayerTimingAdmin(admin.ModelAdmin):
    list_display = (
        "city",
        "date",
        "fajr_time",
        "sunrise_time",
        "dhuhr_time",
        "asr_time",
        "maghrib_time",
        "isha_time",
    )
    list_filter = ("city", "date")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CityCalendarImportLog)
class CityCalendarImportLogAdmin(admin.ModelAdmin):
    list_display = (
        "city",
        "filename",
        "rows_processed",
        "rows_created",
        "rows_updated",
        "rows_skipped",
        "status",
        "uploaded_by",
        "created_at",
    )
    list_filter = ("city", "status", "created_at")
    readonly_fields = (
        "city",
        "filename",
        "rows_processed",
        "rows_created",
        "rows_updated",
        "rows_skipped",
        "status",
        "uploaded_by",
        "created_at",
        "updated_at",
    )

