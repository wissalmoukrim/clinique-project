from django.db import models
from patients.models import Patient

class Facture(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    payee = models.BooleanField(default=False)

    def __str__(self):
        return f"Facture {self.id} - {self.patient}"
    
class Paiement(models.Model):
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date_paiement = models.DateField(auto_now_add=True)
    methode = models.CharField(max_length=50)

    def __str__(self):
        return f"Paiement {self.id}"