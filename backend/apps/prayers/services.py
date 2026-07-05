"""Prayer write workflows and dynamic congregation timing resolvers live here."""

from dataclasses import dataclass
from datetime import date, time, datetime, timedelta

@dataclass
class ResolvedPrayerTiming:
    fajr_time: time
    dhuhr_time: time
    asr_time: time
    maghrib_time: time
    isha_time: time
    jumuah_time: time
    effective_from: date
    maghrib_congregation_mode: str

def ensure_time(t) -> time:
    """Helper to convert string time representation to datetime.time if necessary."""
    if isinstance(t, time):
        return t
    if isinstance(t, str):
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(t, fmt).time()
            except ValueError:
                pass
    raise ValueError(f"Could not convert {t} to datetime.time")

def add_minutes_to_time(t, minutes: int) -> time:
    """Safely adds minutes to a datetime.time or string time object, handling rollovers."""
    t_obj = ensure_time(t)
    total_minutes = t_obj.hour * 60 + t_obj.minute + minutes
    # Handle rollover (wrap around 24 hours)
    total_minutes = total_minutes % (24 * 60)
    new_hour = total_minutes // 60
    new_minute = total_minutes % 60
    return time(new_hour, new_minute, t_obj.second)

class CongregationTimingResolver:
    @staticmethod
    def resolve_prayer_timing(timing, date_val: date) -> ResolvedPrayerTiming | None:
        """Resolves the effective congregation timings for a PrayerTiming record on a specific date.
        
        If Maghrib is set to CITY_OFFSET, reads the Maghrib start time from the citywide daily timetable
        and offsets it. Otherwise, returns the manually configured static values.
        """
        if not timing:
            return None

        # Start with static values from the database
        resolved_maghrib = ensure_time(timing.maghrib_time)
        
        # Check if city-level auto calculation is active for this mosque
        from apps.prayers.models import PrayerTiming
        if timing.maghrib_congregation_mode == PrayerTiming.CongregationMode.CITY_OFFSET:
            mosque = timing.mosque
            city = mosque.city_relation if mosque else None
            if city and city.maghrib_auto_congregation_enabled:
                from apps.locations.models import CityDailyPrayerTiming
                daily_timing = CityDailyPrayerTiming.objects.filter(
                    city=city,
                    date=date_val
                ).first()
                if daily_timing:
                    resolved_maghrib = add_minutes_to_time(
                        daily_timing.maghrib_time,
                        city.maghrib_congregation_offset
                    )

        return ResolvedPrayerTiming(
            fajr_time=ensure_time(timing.fajr_time),
            dhuhr_time=ensure_time(timing.dhuhr_time),
            asr_time=ensure_time(timing.asr_time),
            maghrib_time=resolved_maghrib,
            isha_time=ensure_time(timing.isha_time),
            jumuah_time=ensure_time(timing.jumuah_time),
            effective_from=timing.effective_from,
            maghrib_congregation_mode=timing.maghrib_congregation_mode,
        )
