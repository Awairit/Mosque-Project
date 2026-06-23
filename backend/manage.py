#!/usr/bin/env python
"""Django's command-line utility for this project."""

import os
import sys


def main() -> None:
    """Run administrative tasks such as runserver, migrate, and createsuperuser."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Make sure dependencies are installed and your "
            "virtual environment is activated."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
