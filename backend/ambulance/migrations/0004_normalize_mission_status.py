from django.db import migrations, models


def normalize_status(apps, schema_editor):
    MissionAmbulance = apps.get_model("ambulance", "MissionAmbulance")
    MissionAmbulance.objects.filter(statut="en cours").update(statut="en_cours")
    MissionAmbulance.objects.filter(statut="terminée").update(statut="terminee")


class Migration(migrations.Migration):

    dependencies = [
        ("ambulance", "0003_alter_ambulance_matricule_alter_ambulance_type_and_more"),
    ]

    operations = [
        migrations.RunPython(normalize_status, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="missionambulance",
            name="statut",
            field=models.CharField(
                choices=[
                    ("en_attente", "En attente"),
                    ("en_cours", "En cours"),
                    ("terminee", "Terminee"),
                ],
                default="en_attente",
                max_length=20,
            ),
        ),
    ]
