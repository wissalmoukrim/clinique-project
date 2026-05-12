import json

from django.test import TestCase
from django.urls import reverse

from core.models import AuditLog

from .models import User


class AuthSecurityTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="Strong!123", role="admin")
        self.patient = User.objects.create_user(username="patient", password="Strong!123", role="patient")

    def test_jwt_login_locks_account_after_repeated_failures(self):
        url = reverse("jwt_login")
        for _ in range(5):
            response = self.client.post(
                url,
                data=json.dumps({"username": "patient", "password": "wrong"}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 401)

        self.patient.refresh_from_db()
        self.assertTrue(self.patient.is_locked)
        self.assertTrue(AuditLog.objects.filter(action="login_failed", user=self.patient).exists())

    def test_register_rejects_weak_password(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("register"),
            data=json.dumps({"username": "weak", "password": "Password1", "role": "patient"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username="weak").exists())

    def test_change_password_requires_current_password(self):
        self.client.force_login(self.patient)
        response = self.client.post(
            reverse("change_password"),
            data=json.dumps({"current_password": "wrong", "new_password": "NewStrong!123"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(AuditLog.objects.filter(action="security_alert", user=self.patient).exists())
