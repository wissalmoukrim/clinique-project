from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hospitalisation", "0005_normalize_hospitalisation_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="hospitalisation",
            name="frequence_cardiaque",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="hospitalisation",
            name="observations",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="hospitalisation",
            name="temperature",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
        migrations.AddField(
            model_name="hospitalisation",
            name="tension",
            field=models.CharField(blank=True, default="", max_length=20),
        ),
    ]
