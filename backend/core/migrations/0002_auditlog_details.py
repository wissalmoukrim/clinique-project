from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("login", "Login"),
                    ("logout", "Logout"),
                    ("create", "Create"),
                    ("update", "Update"),
                    ("delete", "Delete"),
                    ("register", "Register"),
                ],
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="details",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="ip_address",
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="object_id",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="resource",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
