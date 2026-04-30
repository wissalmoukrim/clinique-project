from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "resource", "object_id", "ip_address")
    list_filter = ("action", "resource", "timestamp")
    search_fields = ("user__username", "resource", "object_id", "details")
