from django.contrib import admin
from apps.platform_admin.models import MosqueApprovalLog


@admin.register(MosqueApprovalLog)
class MosqueApprovalLogAdmin(admin.ModelAdmin):
    list_display = ["action", "mosque_name", "admin", "created_at"]
    list_filter = ["action", "created_at"]
    search_fields = ["mosque_name", "admin__username"]
