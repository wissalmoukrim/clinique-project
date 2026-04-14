from django.db import models
from rendezvous.models import RendezVous
from medecins.models import Medecin

class Consultation(models.Model):
    rendezvous = models.ForeignKey(RendezVous, on_delete=models.CASCADE)
    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    diagnostic = models.TextField()
    notes = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Consultation {self.id} - {self.medecin}"
    
class Ordonnance(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Ordonnance {self.id}"
    
class Medicament(models.Model):
    ordonnance = models.ForeignKey(Ordonnance, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)
    duree = models.CharField(max_length=50)

    def __str__(self):
        return self.nom