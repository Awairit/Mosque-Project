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
    maghrib_delay_minutes: int = 15


def ensure_time(t) -> time | None:
    """Helper to convert string or time representation to datetime.time safely."""
    if t is None:
        return None
    if isinstance(t, time):
        return t
    if isinstance(t, str):
        t_str = t.strip()
        if not t_str:
            return None
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(t_str, fmt).time()
            except ValueError:
                pass
    return None


def add_minutes_to_time(t, minutes: int) -> time | None:
    """Safely adds minutes to a datetime.time or string time object, handling rollovers."""
    t_obj = ensure_time(t)
    if t_obj is None:
        return None
    dt = datetime.combine(date.today(), t_obj) + timedelta(minutes=minutes)
    return dt.time()


class PrayerTimingService:
    """Encapsulates prayer timing resolution business logic."""

    @staticmethod
    def resolve_timing(timing, date_val: date = None) -> ResolvedPrayerTiming | None:
        if not timing:
            return None
        if date_val is None:
            date_val = date.today()

        city = timing.mosque.city_relation if timing.mosque else None
        delay_mins = getattr(timing, "maghrib_delay_minutes", 15) or 15
        state_key = (
            timing.maghrib_congregation_mode,
            timing.maghrib_time,
            delay_mins,
            city.maghrib_auto_congregation_enabled if city else None,
            city.maghrib_congregation_offset if city else None,
        )

        cache_key = f"_resolved_{date_val.isoformat()}"
        if hasattr(timing, cache_key):
            cached_resolved, cached_state = getattr(timing, cache_key)
            if cached_state == state_key:
                return cached_resolved

        # Start with static values from the database
        resolved_maghrib = ensure_time(timing.maghrib_time)

        # Check if city-level / offset calculation is active for this mosque
        from apps.prayers.models import PrayerTiming
        if timing.maghrib_congregation_mode == PrayerTiming.CongregationMode.CITY_OFFSET:
            if city and city.maghrib_auto_congregation_enabled:
                daily_timing = None
                today_timings = getattr(city, "today_daily_timing", None)
                if today_timings is not None:
                    if len(today_timings) > 0 and today_timings[0].date == date_val:
                        daily_timing = today_timings[0]

                if daily_timing is None:
                    from apps.locations.models import CityDailyPrayerTiming
                    daily_timing = CityDailyPrayerTiming.objects.filter(
                        city=city,
                        date=date_val
                    ).first()

                if daily_timing and daily_timing.maghrib_time:
                    # If mosque has explicitly configured delay (differs from default 15) or city offset is set
                    if delay_mins != 15:
                        offset_to_use = delay_mins
                    elif city and city.maghrib_congregation_offset is not None:
                        offset_to_use = city.maghrib_congregation_offset
                    else:
                        offset_to_use = delay_mins

                    offset_maghrib = add_minutes_to_time(
                        daily_timing.maghrib_time,
                        offset_to_use
                    )
                    if offset_maghrib:
                        resolved_maghrib = offset_maghrib

        fajr = ensure_time(timing.fajr_time)
        dhuhr = ensure_time(timing.dhuhr_time)
        asr = ensure_time(timing.asr_time)
        maghrib = resolved_maghrib
        isha = ensure_time(timing.isha_time)
        jumuah = ensure_time(timing.jumuah_time)

        # If any prayer time field is missing or unparseable, resolution is incomplete.
        if not all([fajr, dhuhr, asr, maghrib, isha, jumuah]):
            return None

        eff_from = timing.effective_from or date_val

        resolved = ResolvedPrayerTiming(
            fajr_time=fajr,
            dhuhr_time=dhuhr,
            asr_time=asr,
            maghrib_time=maghrib,
            isha_time=isha,
            jumuah_time=jumuah,
            effective_from=eff_from,
            maghrib_congregation_mode=timing.maghrib_congregation_mode or PrayerTiming.CongregationMode.MANUAL,
            maghrib_delay_minutes=delay_mins,
        )

        setattr(timing, cache_key, (resolved, state_key))
        return resolved


class CongregationTimingResolver:
    """Backwards-compatibility resolver alias for PrayerTimingService."""

    @staticmethod
    def resolve_prayer_timing(timing, date_val: date = None) -> ResolvedPrayerTiming | None:
        if not timing:
            return None
        return PrayerTimingService.resolve_timing(timing, date_val)
