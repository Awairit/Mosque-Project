"""Mosque availability engine and read/write workflows."""

from datetime import datetime, date, timedelta
import re
import urllib.request
import django.utils.timezone as django_timezone

from apps.mosques.models import Mosque, MosqueOperatingSchedule
from apps.prayers.models import PrayerTiming


def extract_coordinates_from_url(url: str) -> tuple[float, float] | tuple[None, None]:
    """Resolve redirect URLs and extract coordinates (latitude, longitude) from Google Maps link.

    Supports short links and various long formats. Enforces a 5-second timeout.
    """
    if not url:
        return None, None

    url = url.strip()
    final_url = url

    # 1. Resolve HTTP Redirects for short URLs
    if "maps.app.goo.gl" in url or "goo.gl/maps" in url or "maps.google" in url:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            # Short timeout to avoid hanging django threads
            with urllib.request.urlopen(req, timeout=5) as response:
                final_url = response.geturl()
        except Exception:
            # Fallback to direct parsing if resolution fails (e.g. offline dev environments)
            pass

    # 2. Extract coordinates using Regex patterns
    # Pattern A: Standard @latitude,longitude suffix
    match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
    if match:
        return float(match.group(1)), float(match.group(2))

    # Pattern B: Query parameters (e.g., query=lat,lon or q=lat,lon or ll=lat,lon)
    match = re.search(r"[?&](query|q|ll)=(-?\d+\.\d+),(-?\d+\.\d+)", final_url)
    if match:
        return float(match.group(2)), float(match.group(3))

    # Pattern C: Place path parameters (e.g., place/lat,lon or place/lat+lon)
    match = re.search(r"place/(-?\d+\.\d+)[,+](-?\d+\.\d+)", final_url)
    if match:
        return float(match.group(1)), float(match.group(2))

    # Pattern D: Internal maps 3d/4d parameters (e.g. !3d19.1578291!4d77.3353815)
    match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", final_url)
    if match:
        return float(match.group(1)), float(match.group(2))

    return None, None


class MosqueAvailabilityEngine:
    """Calculates real-time open status and next prayer information for a Mosque."""

    _timezone_cache = {}

    @classmethod
    def get_city_timezone(cls, city) -> str:
        if not city:
            return "Asia/Kolkata"
        if isinstance(city, str):
            key = city.lower().strip()
            if key not in cls._timezone_cache:
                from apps.locations.models import City
                city_obj = City.objects.filter(name__iexact=key).first()
                cls._timezone_cache[key] = city_obj.timezone if (city_obj and city_obj.timezone) else "Asia/Kolkata"
            return cls._timezone_cache[key]
        else:
            # Handle locations.City object directly
            return city.timezone if city.timezone else "Asia/Kolkata"

    def __init__(self, mosque: Mosque, current_dt=None):
        self.mosque = mosque
        
        from zoneinfo import ZoneInfo
        
        city_ref = self.mosque.city_relation if self.mosque.city_relation else self.mosque.city
        self.tz_name = self.get_city_timezone(city_ref)
        
        if current_dt is None:
            self.current_dt = django_timezone.now().astimezone(ZoneInfo(self.tz_name))
        else:
            if django_timezone.is_aware(current_dt):
                self.current_dt = current_dt.astimezone(ZoneInfo(self.tz_name))
            else:
                self.current_dt = current_dt
        
        self.current_time = self.current_dt.time()
        self.current_date = self.current_dt.date()

    def get_availability(self) -> dict:
        """Evaluates operational status and next prayer details.

        Returns standard availability operational schema.
        """
        # Part 1: Open / Closed Status
        is_open = False
        status_label = "Closed"
        current_window = None
        closes_at = None
        opens_at = None

        try:
            schedule = self.mosque.operating_schedule
        except MosqueOperatingSchedule.DoesNotExist:
            schedule = None

        if schedule is None:
            is_open = False
            status_label = "Schedule Not Verified"
        elif schedule.open_24_hours:
            is_open = True
            status_label = "Open 24 Hours"
        else:
            # Gather valid windows
            windows = [
                ("fajr", schedule.fajr_open, schedule.fajr_close),
                ("dhuhr", schedule.dhuhr_open, schedule.dhuhr_close),
                ("asr", schedule.asr_open, schedule.asr_close),
                ("maghrib", schedule.maghrib_open, schedule.maghrib_close),
                ("isha", schedule.isha_open, schedule.isha_close),
            ]
            valid_windows = []
            for name, open_t, close_t in windows:
                if open_t is not None and close_t is not None:
                    valid_windows.append((name, open_t, close_t))

            if not valid_windows:
                is_open = False
                status_label = "Schedule Not Verified"
            else:
                active_window = None
                # Check if we are inside any window
                for name, open_t, close_t in valid_windows:
                    if open_t <= close_t:
                        if open_t <= self.current_time <= close_t:
                            active_window = (name, open_t, close_t)
                            break
                    else:
                        # Overnight window
                        if self.current_time >= open_t or self.current_time <= close_t:
                            active_window = (name, open_t, close_t)
                            break

                if active_window is not None:
                    name, open_t, close_t = active_window
                    is_open = True
                    current_window = name
                    closes_at = close_t.strftime("%I:%M %p")

                    # Calculate "Closing Soon" (within 15 minutes of closing)
                    try:
                        dt_current = datetime.combine(date.today(), self.current_time)
                        dt_close = datetime.combine(date.today(), close_t)
                        # Adjust for midnight wrap
                        if close_t < open_t and self.current_time <= close_t:
                            dt_current = datetime.combine(date.today() - timedelta(days=1), self.current_time)
                        
                        diff_minutes = (dt_close - dt_current).total_seconds() / 60.0
                        if 0.0 <= diff_minutes <= 15.0:
                            status_label = "Closing Soon"
                        else:
                            status_label = "Open Now"
                    except Exception:
                        status_label = "Open Now"
                else:
                    is_open = False
                    status_label = "Closed"

                    # Find next open time today or tomorrow
                    valid_windows.sort(key=lambda x: x[1])
                    next_open = None
                    for name, open_t, close_t in valid_windows:
                        if open_t > self.current_time:
                            next_open = open_t
                            break

                    if next_open is None:
                        next_open = valid_windows[0][1]

                    opens_at = next_open.strftime("%I:%M %p")

        # Part 2: Next Prayer (Jamaat) Timings
        next_prayer_name = None
        next_prayer_time = None

        from apps.prayers.models import PrayerTiming
        try:
            timing = self.mosque.prayer_timing
        except PrayerTiming.DoesNotExist:
            timing = None

        from apps.prayers.services import CongregationTimingResolver
        resolved = CongregationTimingResolver.resolve_prayer_timing(timing, self.current_date)

        if resolved is not None:
            prayers = [
                ("Fajr", resolved.fajr_time),
                ("Dhuhr", resolved.dhuhr_time),
                ("Asr", resolved.asr_time),
                ("Maghrib", resolved.maghrib_time),
                ("Isha", resolved.isha_time),
            ]
            # Find next prayer today
            next_p = None
            for name, p_time in prayers:
                if p_time > self.current_time:
                    next_p = (name, p_time)
                    break

            if next_p is None:
                # Rollover to tomorrow's Fajr
                next_prayer_name = "Fajr"
                next_prayer_time = resolved.fajr_time.strftime("%I:%M %p")
            else:
                next_prayer_name = next_p[0]
                next_prayer_time = next_p[1].strftime("%I:%M %p")

        return {
            "is_open": is_open,
            "status_label": status_label,
            "current_window": current_window,
            "closes_at": closes_at,
            "opens_at": opens_at,
            "next_prayer_name": next_prayer_name,
            "next_prayer_time": next_prayer_time,
        }
