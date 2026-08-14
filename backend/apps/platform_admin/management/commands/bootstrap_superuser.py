import os
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Safely bootstrap an initial superuser from environment variables if none exists."

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS("Superuser already exists. Skipping bootstrap."))
            return

        username = os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "admin")
        email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "admin@mosquecom.com")
        password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")

        if not password:
            self.stderr.write(self.style.ERROR("BOOTSTRAP_ADMIN_PASSWORD environment variable is not set."))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' successfully created."))
