from django.db import models
from personnel.models import Personnel


# ================= VISITEUR =================
class Visiteur(models.Model):
    nom = models.CharField(max_length=100, null=True, blank=True)
    prenom = models.CharField(max_length=100, null=True, blank=True)

    cin = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )

    telephone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"


# ================= JOURNAL VISITE =================
class JournalVisite(models.Model):
    visiteur = models.ForeignKey(Visiteur, on_delete=models.CASCADE)

    agent_securite = models.ForeignKey(
        Personnel,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={"fonction": "securite"}
    )

    motif = models.CharField(max_length=255, default="visite")

    date_entree = models.DateTimeField(auto_now_add=True)
    date_sortie = models.DateTimeField(null=True, blank=True)

    STATUT_CHOICES = [
        ("en cours", "En cours"),
        ("terminé", "Terminé"),
    ]

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="en cours"
    )

    def __str__(self):
        return f"{self.visiteur} - {self.statut}"