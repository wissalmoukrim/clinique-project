from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "resource", "object_id", "status", "ip_address")
    list_filter = ("action", "resource", "status", "timestamp")
    search_fields = ("user__username", "resource", "object_id", "details")
    readonly_fields = ("user", "action", "resource", "resource_id", "object_id", "details", "ip_address", "status", "timestamp")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
