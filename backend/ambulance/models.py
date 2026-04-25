from django.db import models
from personnel.models import Personnel


# ================= AMBULANCE =================
class Ambulance(models.Model):
    matricule = models.CharField(
        max_length=50,
        unique=True,
        default="AMB-XXX"
    )

    type = models.CharField(
        max_length=50,
        default="standard"
    )

    disponible = models.BooleanField(default=True)

    chauffeur = models.ForeignKey(
        Personnel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={"fonction": "chauffeur"}
    )

    def __str__(self):
        return f"{self.matricule} - {self.type}"


# ================= MISSION AMBULANCE =================
class MissionAmbulance(models.Model):
    ambulance = models.ForeignKey(Ambulance, on_delete=models.CASCADE)

    chauffeur = models.ForeignKey(
        Personnel,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"fonction": "chauffeur"}
    )

    patient_nom = models.CharField(
        max_length=100,
        default="inconnu"
    )

    lieu_depart = models.CharField(
        max_length=255,
        default="domicile"
    )

    lieu_arrivee = models.CharField(
        max_length=255,
        default="clinique"
    )

    date = models.DateTimeField(auto_now_add=True)

    STATUT_CHOICES = [
        ("en cours", "En cours"),
        ("terminée", "Terminée"),
    ]

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="en cours"
    )

    def __str__(self):
        return f"Mission {self.id} - {self.patient_nom}"