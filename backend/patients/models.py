from django.db import models
from accounts.models import User


# ================= PATIENT =================
class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    date_naissance = models.DateField(null=True, blank=True)
    sexe = models.CharField(max_length=10, blank=True)

    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.CharField(max_length=255, blank=True)

    # infos médicales
    groupe_sanguin = models.CharField(max_length=5, blank=True)
    allergies = models.TextField(blank=True)
    antecedents = models.TextField(blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username