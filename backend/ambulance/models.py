from django.db import models
from accounts.models import User
from patients.models import Patient

class Ambulance(models.Model):
    numero = models.CharField(max_length=50)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return self.numero
    
class Chauffeur(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20)

    def __str__(self):
        return self.user.username
    
class MissionAmbulance(models.Model):
    ambulance = models.ForeignKey(Ambulance, on_delete=models.CASCADE)
    chauffeur = models.ForeignKey(Chauffeur, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateField()
    destination = models.CharField(max_length=200)

    def __str__(self):
        return f"Mission {self.id}"