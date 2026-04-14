from django.db import models
from patients.models import Patient

class Chambre(models.Model):
    numero = models.IntegerField()
    type = models.CharField(max_length=50)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"Chambre {self.numero}"
    
class Hospitalisation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    chambre = models.ForeignKey(Chambre, on_delete=models.CASCADE)
    date_entree = models.DateField()
    date_sortie = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.patient} - Chambre {self.chambre.numero}"