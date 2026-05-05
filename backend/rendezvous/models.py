from django.db import models


class RendezVous(models.Model):

    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE)
    medecin = models.ForeignKey("medecins.Medecin", on_delete=models.CASCADE)

    date = models.DateField()
    heure = models.TimeField()

    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("confirme", "Confirme"),
        ("annule", "Annule"),
        ("termine", "Termine"),
    ]

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default="en_attente"
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} → {self.medecin} ({self.date} {self.heure})"
