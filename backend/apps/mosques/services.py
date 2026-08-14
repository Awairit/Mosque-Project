"""Mosque availability engine and read/write workflows."""

from datetime import datetime, date, timedelta
import re
import urllib.request
import django.utils.timezone as django_timezone

from apps.mosques.models import Mosque, MosqueOperatingSchedule
from apps.prayers.models import PrayerTiming


import ipaddress
import re
from urllib.parse import urlparse, unquote

ALLOWED_MAP_HOSTS = {
    "maps.google.com",
    "www.google.com",
    "google.com",
    "maps.app.goo.gl",
    "goo.gl",
}

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def is_allowed_google_maps_url(url: str) -> bool:
    """Validate that URL uses http/https, targets allowed domains, and avoids private IPs (SSRF protection)."""
    if not url:
        return False
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = (parsed.hostname or "").lower()
        if not hostname or hostname == "localhost":
            return False

        # Reject direct IP address targets or internal subnets
        try:
            ip_obj = ipaddress.ip_address(hostname)
            for net in BLOCKED_IP_NETWORKS:
                if ip_obj in net:
                    return False
            return False  # Direct IP targets are not valid Google Maps domains
        except ValueError:
            pass  # Standard hostname string

        # Domain whitelist check
        if hostname in ALLOWED_MAP_HOSTS:
            return True
        if hostname.endswith(".google.com") or hostname.endswith(".google.co.in") or hostname.endswith(".goo.gl"):
            return True

        return False
    except Exception:
        return False


class _SafeGoogleMapsRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow Google Maps redirects only when every redirect target is trusted."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = newurl
        if not is_allowed_google_maps_url(target):
            raise ValueError("Blocked non-Google Maps redirect target")
        return super().redirect_request(req, fp, code, msg, headers, target)


def _resolve_google_maps_short_link(url: str) -> str:
    """Resolve a Google Maps short link through validated Google-only redirects."""
    if not url or not is_allowed_google_maps_url(url):
        return url

    parsed = urlparse(url.strip())
    hostname = (parsed.hostname or "").lower()
    if hostname not in {"maps.app.goo.gl", "goo.gl"} and not hostname.endswith(".goo.gl"):
        return url

    try:
        opener = urllib.request.build_opener(_SafeGoogleMapsRedirectHandler())
        request = urllib.request.Request(
            url.strip(),
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with opener.open(request, timeout=5) as response:
            final_url = response.geturl()
        if is_allowed_google_maps_url(final_url):
            return final_url
    except Exception:
        pass

    return url


def extract_coordinates_from_url(url: str) -> tuple[float, float] | tuple[None, None]:
    """Extract latitude/longitude from Google Maps URLs, including short-link redirects.

    Long Google Maps URLs and raw coordinate strings are parsed locally. Google Maps
    short links are resolved only through redirects whose targets remain on trusted
    Google Maps domains, with a 5-second timeout and SSRF protections.
    """
    if not url:
        return None, None

    url_str = unquote(url.strip())
    url_str = unquote(_resolve_google_maps_short_link(url_str))

    # Raw coordinate string format: "19.157829, 77.335382" or "19.157829,77.335382"
    raw_match = re.match(r"^\s*(-?\d{1,2}\.\d+)\s*[, ]\s*(-?\d{1,3}\.\d+)\s*$", url_str)
    if raw_match:
        try:
            lat = float(raw_match.group(1))
            lon = float(raw_match.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                return round(lat, 6), round(lon, 6)
        except ValueError:
            pass

    if not is_allowed_google_maps_url(url):
        return None, None

    # Pattern A: Standard @latitude,longitude suffix (e.g. /@19.157829,77.335382,17z)
    match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", url_str)
    if match:
        return round(float(match.group(1)), 6), round(float(match.group(2)), 6)

    # Pattern B: Query parameters (e.g., query=lat,lon, q=lat,lon, q=loc:lat,lon, ll=lat,lon, center=lat,lon, daddr=lat,lon)
    match = re.search(r"[?&](query|q|ll|center|saddr|daddr|destination|near|loc)=(?:loc:)?(-?\d+\.\d+)[,+](-?\d+\.\d+)", url_str)
    if match:
        return round(float(match.group(2)), 6), round(float(match.group(3)), 6)

    # Pattern C: Place path parameters (e.g., place/lat,lon or place/lat+lon)
    match = re.search(r"place/(-?\d+\.\d+)[,+](-?\d+\.\d+)", url_str)
    if match:
        return round(float(match.group(1)), 6), round(float(match.group(2)), 6)

    # Pattern D: Internal maps 3d/4d parameters (e.g. !3d19.1578291!4d77.3353815)
    match = re.search(r"!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)", url_str)
    if match:
        return round(float(match.group(1)), 6), round(float(match.group(2)), 6)

    # Pattern E: Internal maps 2d/3d parameters (e.g. !2d77.3353815!3d19.1578291)
    match = re.search(r"!2d(-?\d+\.\d+)!3d(-?\d+\.\d+)", url_str)
    if match:
        return round(float(match.group(2)), 6), round(float(match.group(1)), 6)

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
        elif schedule.open_24_hours or schedule.schedule_mode == "24_HOURS":
            is_open = True
            status_label = "Open 24 Hours"
        elif schedule.schedule_mode == "GENERAL":
            open_t = schedule.general_open_time
            close_t = schedule.general_close_time
            if open_t is None or close_t is None:
                is_open = False
                status_label = "Schedule Not Verified"
            else:
                is_inside = False
                if open_t <= close_t:
                    is_inside = (open_t <= self.current_time <= close_t)
                else:
                    is_inside = (self.current_time >= open_t or self.current_time <= close_t)

                if is_inside:
                    is_open = True
                    closes_at = close_t.strftime("%I:%M %p")
                    try:
                        dt_current = datetime.combine(date.today(), self.current_time)
                        dt_close = datetime.combine(date.today(), close_t)
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
                    opens_at = open_t.strftime("%I:%M %p")
        else:
            # Gather valid windows for SALAH_BASED mode
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


def approve_mosque_registration_request(request_obj, approved_by_user=None):
    """Authoritative service method to approve a MosqueRegistrationRequest.

    Materializes the Mosque, User, and MosqueAdmin records cleanly with geographic
    coordinates derived from registration inputs or Google Maps URL parsing.
    Handles transaction atomicity and row locking safely.
    """
    from django.db import transaction
    from django.db.models import Q
    from django.contrib.auth.models import User
    from django.utils import timezone
    from datetime import timedelta
    import string
    import secrets

    from apps.accounts.models import MosqueAdmin, PasswordAuditLog, IdentityAuditLog
    from apps.platform_admin.models import MosqueApprovalLog
    from apps.mosques.models import MosqueRegistrationRequest, Mosque

    with transaction.atomic():
        req_locked = MosqueRegistrationRequest.objects.select_for_update().filter(pk=request_obj.pk).first()
        if req_locked:
            request_obj = req_locked

        username = request_obj.mobile_number.strip()
        local_digits = username.replace("+91", "")
        e164_variant = f"+91{local_digits}" if not username.startswith("+91") else username

        existing_user_mobile = User.objects.filter(
            Q(username=username) | Q(username=local_digits) | Q(username=e164_variant)
        ).first()

        temp_password = None
        password_generated = False
        user_created = False

        if existing_user_mobile and hasattr(existing_user_mobile, 'mosque_admin'):
            user = existing_user_mobile
        else:
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
            while True:
                temp_password = "".join(secrets.choice(alphabet) for _ in range(14))
                if (any(c.islower() for c in temp_password)
                        and any(c.isupper() for c in temp_password)
                        and any(c.isdigit() for c in temp_password)
                        and any(c in "!@#$%^&*()_+-=" for c in temp_password)):
                    break

            password_generated = True
            email = request_obj.email.strip() if request_obj.email else ""
            if existing_user_mobile:
                user = existing_user_mobile
            else:
                user, user_created = User.objects.get_or_create(username=username)

            if email:
                user.email = email
            user.set_password(temp_password)
            user.is_active = True
            user.save()

        # Extract coordinates from URL or registration fields
        google_maps_url = request_obj.google_maps_url or request_obj.google_maps_link
        lat = getattr(request_obj, "latitude", None)
        lon = getattr(request_obj, "longitude", None)

        if (lat is None or lon is None) and google_maps_url:
            extracted_lat, extracted_lon = extract_coordinates_from_url(google_maps_url)
            if extracted_lat is not None and extracted_lon is not None:
                lat = extracted_lat
                lon = extracted_lon

        # Idempotently find or create the Mosque
        mosque_qs = Mosque.objects.filter(
            mosque_name__iexact=request_obj.mosque_name,
            address__iexact=request_obj.address,
        )
        if request_obj.city_relation:
            mosque = mosque_qs.filter(city_relation=request_obj.city_relation).first()
        else:
            mosque = mosque_qs.filter(city__iexact=request_obj.city).first()

        if not mosque:
            mosque = Mosque.objects.create(
                mosque_name=request_obj.mosque_name,
                city=request_obj.city,
                city_relation=request_obj.city_relation,
                address=request_obj.address,
                google_maps_url=google_maps_url,
                latitude=lat,
                longitude=lon,
                women_prayer_available=request_obj.women_prayer_available,
                mosque_status=Mosque.MosqueStatus.ACTIVE,
            )
        else:
            updated = False
            if google_maps_url and not mosque.google_maps_url:
                mosque.google_maps_url = google_maps_url
                updated = True
            if lat is not None and mosque.latitude is None:
                mosque.latitude = lat
                updated = True
            if lon is not None and mosque.longitude is None:
                mosque.longitude = lon
                updated = True
            if updated:
                mosque.save()

        # Idempotently create MosqueAdmin
        mosque_admin, admin_created = MosqueAdmin.objects.get_or_create(
            user=user,
            defaults={
                "mosque": mosque,
                "mobile_number": request_obj.mobile_number,
                "is_active": True,
            }
        )

        admin_user = approved_by_user if isinstance(approved_by_user, User) else None

        if password_generated:
            mosque_admin.must_change_password = True
            mosque_admin.temporary_password_expires_at = timezone.now() + timedelta(days=7)
            mosque_admin.save()

            PasswordAuditLog.objects.create(
                user=user,
                performed_by=admin_user,
                action=PasswordAuditLog.ActionTypes.GENERATED
            )

        # Mark request as Approved
        request_obj.status = MosqueRegistrationRequest.Status.APPROVED
        request_obj.approved_by = admin_user
        request_obj.approved_at = timezone.now()
        request_obj.save()

        # Create audit records
        audit_admin = admin_user or User.objects.filter(is_superuser=True).first()
        if audit_admin:
            MosqueApprovalLog.objects.create(
                action=MosqueApprovalLog.ActionTypes.APPROVE,
                mosque=mosque,
                registration_request_id=request_obj.id,
                mosque_name=request_obj.mosque_name,
                admin=audit_admin,
            )

        if admin_user:
            IdentityAuditLog.objects.create(
                user=admin_user,
                action=IdentityAuditLog.Action.REGISTRATION_APPROVED,
                metadata={
                    "registration_request_id": request_obj.id,
                    "mosque_name": request_obj.mosque_name,
                    "approved_by": admin_user.username,
                }
            )

        return {
            "mosque": mosque,
            "user": user,
            "mosque_admin": mosque_admin,
            "temp_password": temp_password,
            "user_created": user_created,
        }
