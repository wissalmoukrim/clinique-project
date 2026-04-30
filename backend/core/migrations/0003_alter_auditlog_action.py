from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_auditlog_details"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("login", "Login"),
                    ("logout", "Logout"),
                    ("login_failed", "Login failed"),
                    ("forbidden_access", "Forbidden access"),
                    ("sensitive_access", "Sensitive data access"),
                    ("security_alert", "Security alert"),
                    ("create", "Create"),
                    ("update", "Update"),
                    ("delete", "Delete"),
                    ("register", "Register"),
                ],
                max_length=50,
            ),
        ),
    ]
