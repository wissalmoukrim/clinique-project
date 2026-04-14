from django.db import models
from patients.models import Patient
from medecins.models import Medecin

class RendezVous(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    date = models.DateField()
    heure = models.TimeField()
    statut = models.CharField(max_length=20, default='en attente')

    def __str__(self):
        return f"{self.patient} - {self.medecin} - {self.date}"