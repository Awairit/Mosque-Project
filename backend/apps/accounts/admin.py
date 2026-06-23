"""Django admin registrations for account workflows."""

from django.contrib import admin
from django.utils.crypto import get_random_string

from apps.accounts.models import MosqueAdmin


@admin.register(MosqueAdmin)
class MosqueAdminAdmin(admin.ModelAdmin):
    list_display = (
        "mobile_number",
        "get_username",
        "get_mosque_name",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("mobile_number", "user__username", "mosque__mosque_name")
    readonly_fields = ("created_at", "updated_at")
    actions = ("reset_credentials", "disable_accounts", "enable_accounts")

    def get_username(self, obj) -> str:
        return obj.user.username

    get_username.short_description = "Username"

    def get_mosque_name(self, obj) -> str:
        return obj.mosque.mosque_name

    get_mosque_name.short_description = "Mosque"

    @admin.action(description="Reset credentials for selected admins")
    def reset_credentials(self, request, queryset):
        reset_count = 0
        for admin_profile in queryset:
            temp_password = get_random_string(length=12)
            admin_profile.user.set_password(temp_password)
            admin_profile.user.save()

            # Display the generated temporary password only through the Django Admin success message
            self.message_user(
                request,
                (
                    f"Reset password for {admin_profile.mobile_number}. "
                    f"New Temporary Password: {temp_password}"
                ),
                level="info",
            )
            reset_count += 1
        self.message_user(
            request,
            f"Successfully reset credentials for {reset_count} account(s).",
        )

    @admin.action(description="Disable selected accounts")
    def disable_accounts(self, request, queryset):
        updated_count = 0
        for admin_profile in queryset:
            admin_profile.is_active = False
            admin_profile.save(update_fields=["is_active", "updated_at"])
            admin_profile.user.is_active = False
            admin_profile.user.save(update_fields=["is_active"])
            updated_count += 1
        self.message_user(request, f"Disabled {updated_count} account(s).")

    @admin.action(description="Enable selected accounts")
    def enable_accounts(self, request, queryset):
        updated_count = 0
        for admin_profile in queryset:
            admin_profile.is_active = True
            admin_profile.save(update_fields=["is_active", "updated_at"])
            admin_profile.user.is_active = True
            admin_profile.user.save(update_fields=["is_active"])
            updated_count += 1
        self.message_user(request, f"Enabled {updated_count} account(s).")
