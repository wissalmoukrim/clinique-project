from django.db import models
from django.utils import timezone


class Medecin(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE)
    specialite = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True)
    numero_ordre = models.CharField(max_length=50, unique=True, null=True, blank=True)
    disponible = models.BooleanField(default=True)
    experience = models.IntegerField(null=True, blank=True, help_text="Années d'expérience")
    date_creation = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username} - {self.specialite}"
