from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_auditlog_login_success_resource_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditlog",
            name="status",
            field=models.CharField(default="success", max_length=20),
        ),
    ]
