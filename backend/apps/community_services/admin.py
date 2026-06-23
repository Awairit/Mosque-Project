from django.contrib import admin
from apps.community_services.models import JanazahNotice


@admin.register(JanazahNotice)
class JanazahNoticeAdmin(admin.ModelAdmin):
    list_display = ["deceased_name", "mosque", "gender", "salah_date", "salah_time", "status"]
    list_filter = ["status", "gender"]
    search_fields = ["deceased_name", "mosque__mosque_name", "cemetery_name"]
    autocomplete_fields = ["mosque"]
