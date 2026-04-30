from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_alter_auditlog_action"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="resource_id",
            field=models.CharField(blank=True, max_length=100),
        ),
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
                    ("create", "Create"),
                    ("update", "Update"),
                    ("delete", "Delete"),
                    ("register", "Register"),
                ],
                max_length=50,
            ),
        ),
    ]
