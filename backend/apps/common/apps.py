import os
import sys
from django.apps import AppConfig
from django.conf import settings


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"

    def ready(self):
        # We only want to print detailed diagnostics in development.
        if not settings.DEBUG:
            return

        # Prevent duplicate prints when runserver's auto-reloader is active
        is_runserver = any(arg == "runserver" for arg in sys.argv)
        if is_runserver and os.environ.get("RUN_MAIN") != "true":
            return

        # Skip printing during typical management commands
        skip_commands = {
            "test",
            "makemigrations",
            "migrate",
            "collectstatic",
            "shell",
            "createsuperuser",
            "check",
        }
        if any(cmd in sys.argv for cmd in skip_commands):
            return

        self._print_startup_banner()

    def _print_startup_banner(self):
        provider_name = getattr(settings, "OTP_PROVIDER", "dummy").strip().lower()
        is_twilio = provider_name == "twilio"

        provider_class = "TwilioVerifyProvider" if is_twilio else "DummyOTPProvider"
        sms_service = "Twilio Verify" if is_twilio else "Local Development (No SMS)"

        account_sid = bool(getattr(settings, "TWILIO_ACCOUNT_SID", False))
        verify_sid = bool(getattr(settings, "TWILIO_VERIFY_SERVICE_SID", False))
        auth_token = bool(getattr(settings, "TWILIO_AUTH_TOKEN", False))

        def status(configured):
            return "✅ Configured" if configured else "❌ Missing"

        banner = [
            "",
            "============================================================",
            "🚀 Mosque Finder Backend Started",
            "",
            "Environment : Development",
            f"OTP Provider: {provider_class}",
            f"SMS Service : {sms_service}",
        ]

        if is_twilio:
            banner.extend(
                [
                    "",
                    f"Twilio Account SID      : {status(account_sid)}",
                    f"Twilio Verify Service   : {status(verify_sid)}",
                    f"Auth Token              : {status(auth_token)}",
                ]
            )
        elif account_sid or verify_sid or auth_token:
            banner.extend(
                [
                    "",
                    f"Twilio Account SID      : {status(account_sid)}",
                    f"Twilio Verify Service   : {status(verify_sid)}",
                    f"Auth Token              : {status(auth_token)}",
                ]
            )

        banner.append("============================================================")
        try:
            print("\n".join(banner))
        except UnicodeEncodeError:
            # Fallback for Windows terminals without UTF-8 support
            safe_banner = "\n".join(banner).encode("ascii", "replace").decode("ascii")
            print(safe_banner)

