"""Services for location-related timing imports and calculations."""

import csv
import io
from datetime import datetime, time
from django.core.files.uploadedfile import UploadedFile


def parse_and_validate_calendar_csv(csv_file, city_id: int) -> dict:
    """Parses and validates a city prayer calendar CSV file in memory.

    Enforces date and time formatting, and timing sequence validation:
    Fajr < Sunrise < Dhuhr < Asr < Maghrib < Isha.

    Returns a dict containing validation status, rows parsed, preview data, and errors.
    """
    errors = []
    parsed_rows = []

    # Read CSV file content
    try:
        if isinstance(csv_file, UploadedFile):
            content = csv_file.read().decode("utf-8-sig")
            csv_file.seek(0)  # Reset pointer
        elif hasattr(csv_file, "read"):
            content = csv_file.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8-sig")
        else:
            content = str(csv_file)
    except Exception as e:
        return {
            "success": False,
            "errors": [f"Could not read CSV file. Make sure it is encoded in UTF-8: {str(e)}"],
            "rows": [],
            "preview": [],
        }

    reader = csv.reader(io.StringIO(content))
    try:
        headers = next(reader)
    except StopIteration:
        return {
            "success": False,
            "errors": ["The CSV file is empty."],
            "rows": [],
            "preview": [],
        }

    # Normalize headers
    normalized_headers = [h.strip().lower() for h in headers]
    required_cols = ["date", "fajr_time", "sunrise_time", "dhuhr_time", "asr_time", "maghrib_time", "isha_time"]

    missing_cols = [col for col in required_cols if col not in normalized_headers]
    if missing_cols:
        return {
            "success": False,
            "errors": [f"Missing required columns in CSV headers: {', '.join(missing_cols)}"],
            "rows": [],
            "preview": [],
        }

    # Map headers to indices
    col_map = {col: normalized_headers.index(col) for col in required_cols}

    def parse_time(time_str: str) -> time | None:
        time_str = time_str.strip()
        for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M%p"):
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                pass
        return None

    # Parse and validate row by row
    line_number = 1  # Header is line 1
    for row in reader:
        line_number += 1
        if not row or all(not cell.strip() for cell in row):
            continue  # Skip empty lines

        # Check column count matches header count (at least enough columns)
        if len(row) <= max(col_map.values()):
            errors.append(f"Row {line_number}: Column count does not match the required columns.")
            continue

        date_str = row[col_map["date"]].strip()
        fajr_str = row[col_map["fajr_time"]].strip()
        sunrise_str = row[col_map["sunrise_time"]].strip()
        dhuhr_str = row[col_map["dhuhr_time"]].strip()
        asr_str = row[col_map["asr_time"]].strip()
        maghrib_str = row[col_map["maghrib_time"]].strip()
        isha_str = row[col_map["isha_time"]].strip()

        # Parse date
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            errors.append(f"Row {line_number}: Invalid date format '{date_str}'. Expected YYYY-MM-DD.")
            continue

        # Parse times
        fajr_t = parse_time(fajr_str)
        sunrise_t = parse_time(sunrise_str)
        dhuhr_t = parse_time(dhuhr_str)
        asr_t = parse_time(asr_str)
        maghrib_t = parse_time(maghrib_str)
        isha_t = parse_time(isha_str)

        time_errors = []
        if not fajr_t:
            time_errors.append(f"Fajr time '{fajr_str}'")
        if not sunrise_t:
            time_errors.append(f"Sunrise time '{sunrise_str}'")
        if not dhuhr_t:
            time_errors.append(f"Dhuhr time '{dhuhr_str}'")
        if not asr_t:
            time_errors.append(f"Asr time '{asr_str}'")
        if not maghrib_t:
            time_errors.append(f"Maghrib time '{maghrib_str}'")
        if not isha_t:
            time_errors.append(f"Isha time '{isha_str}'")

        if time_errors:
            errors.append(f"Row {line_number}: Invalid format for: {', '.join(time_errors)}. Expected HH:MM or HH:MM:SS.")
            continue

        # Chronological prayer order validation
        # Fajr < Sunrise < Dhuhr < Asr < Maghrib < Isha
        if fajr_t >= sunrise_t:
            errors.append(f"Row {line_number}: Fajr time ({fajr_t.strftime('%H:%M')}) must be before Sunrise ({sunrise_t.strftime('%H:%M')}).")
            continue
        if sunrise_t >= dhuhr_t:
            errors.append(f"Row {line_number}: Sunrise time ({sunrise_t.strftime('%H:%M')}) must be before Dhuhr ({dhuhr_t.strftime('%H:%M')}).")
            continue
        if dhuhr_t >= asr_t:
            errors.append(f"Row {line_number}: Dhuhr time ({dhuhr_t.strftime('%H:%M')}) must be before Asr ({asr_t.strftime('%H:%M')}).")
            continue
        if asr_t >= maghrib_t:
            errors.append(f"Row {line_number}: Asr time ({asr_t.strftime('%H:%M')}) must be before Maghrib ({maghrib_t.strftime('%H:%M')}).")
            continue
        if maghrib_t >= isha_t:
            errors.append(f"Row {line_number}: Maghrib time ({maghrib_t.strftime('%H:%M')}) must be before Isha ({isha_t.strftime('%H:%M')}).")
            continue

        parsed_rows.append({
            "date": parsed_date.strftime("%Y-%m-%d"),
            "fajr_time": fajr_t.strftime("%H:%M:%S"),
            "sunrise_time": sunrise_t.strftime("%H:%M:%S"),
            "dhuhr_time": dhuhr_t.strftime("%H:%M:%S"),
            "asr_time": asr_t.strftime("%H:%M:%S"),
            "maghrib_time": maghrib_t.strftime("%H:%M:%S"),
            "isha_time": isha_t.strftime("%H:%M:%S"),
        })

    if errors:
        return {
            "success": False,
            "errors": errors,
            "rows": [],
            "preview": [],
        }

    return {
        "success": True,
        "errors": [],
        "rows": parsed_rows,
        "preview": parsed_rows[:10],
    }
