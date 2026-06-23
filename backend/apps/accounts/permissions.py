"""DRF Permission classes for account-related authorization."""

from rest_framework.permissions import BasePermission


class IsMosqueAdmin(BasePermission):
    """Allows access only to authenticated users who are active Mosque Admins."""

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, "mosque_admin")
            and request.user.mosque_admin.is_active
        )


class IsMosqueAdminOfObject(BasePermission):
    """Allows access only to the Mosque Admin associated with the specific mosque object."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        if not hasattr(request.user, "mosque_admin"):
            return False

        mosque_admin = request.user.mosque_admin
        if not mosque_admin.is_active:
            return False

        # If the object is a Mosque itself
        if hasattr(obj, "admins"):
            return obj.admins.filter(id=mosque_admin.id).exists()

        # If the object has a mosque foreign key
        if hasattr(obj, "mosque"):
            return obj.mosque == mosque_admin.mosque

        return False
