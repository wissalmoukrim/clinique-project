from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "role",
            "action",
            "resource",
            "resource_id",
            "object_id",
            "details",
            "ip_address",
            "status",
            "timestamp",
        ]
        read_only_fields = fields

    def get_user(self, obj):
        return obj.user.username if obj.user else "anonymous"

    def get_role(self, obj):
        return obj.user.role if obj.user else None
