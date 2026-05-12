from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_auditlog_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("login", "Login"),
                    ("login_success", "Login success"),
                    ("logout", "Logout"),
                    ("login_failed", "Login failed"),
                    ("forbidden_access", "Forbidden access"),
                    ("sensitive_access", "Sensitive data access"),
                    ("security_alert", "Security alert"),
                    ("chatbot_query", "Chatbot query"),
                    ("chatbot_blocked", "Chatbot blocked"),
                    ("create", "Create"),
                    ("update", "Update"),
                    ("delete", "Delete"),
                    ("register", "Register"),
                ],
                max_length=50,
            ),
        ),
    ]
