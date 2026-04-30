from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("login", "Login"),
        ("login_success", "Login success"),
        ("logout", "Logout"),
        ("login_failed", "Login failed"),
        ("forbidden_access", "Forbidden access"),
        ("sensitive_access", "Sensitive data access"),
        ("security_alert", "Security alert"),
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("register", "Register"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    resource = models.CharField(max_length=100, blank=True)
    resource_id = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} {self.resource} by {self.user_id or 'anonymous'}"
