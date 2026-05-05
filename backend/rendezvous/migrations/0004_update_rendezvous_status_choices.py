from django.db import migrations, models


def normalize_statuses(apps, schema_editor):
    RendezVous = apps.get_model("rendezvous", "RendezVous")
    mappings = {
        "en attente": "en_attente",
        "validé": "confirme",
        "validÃ©": "confirme",
        "confirme": "confirme",
        "confirmé": "confirme",
        "confirmÃ©": "confirme",
        "annulé": "annule",
        "annulÃ©": "annule",
        "annule": "annule",
    }
    for old_value, new_value in mappings.items():
        RendezVous.objects.filter(statut=old_value).update(statut=new_value)


class Migration(migrations.Migration):

    dependencies = [
        ("rendezvous", "0003_rendezvous_date_creation"),
    ]

    operations = [
        migrations.RunPython(normalize_statuses, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="rendezvous",
            name="statut",
            field=models.CharField(
                choices=[
                    ("en_attente", "En attente"),
                    ("confirme", "Confirme"),
                    ("annule", "Annule"),
                    ("termine", "Termine"),
                ],
                default="en_attente",
                max_length=20,
            ),
        ),
    ]
