from django.db import models
from patients.models import Patient
from consultations.models import Consultation
from hospitalisation.models import Hospitalisation


# ================= FACTURE =================
class Facture(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)

    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    hospitalisation = models.ForeignKey(
        Hospitalisation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    STATUT_CHOICES = [
        ('non payé', 'Non payé'),
        ('payé', 'Payé'),
    ]

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='non payé'
    )

    def __str__(self):
        return f"Facture {self.id} - {self.patient.user.username}"


# ================= PAIEMENT =================
class Paiement(models.Model):
    facture = models.OneToOneField(Facture, on_delete=models.CASCADE)

    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

    MODE_CHOICES = [
        ('cash', 'Cash'),
        ('carte', 'Carte'),
        ('virement', 'Virement'),
    ]

    mode = models.CharField(max_length=20, choices=MODE_CHOICES)

    def __str__(self):
        return f"Paiement {self.facture.id}"