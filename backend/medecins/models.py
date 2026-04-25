from django.db import models
from accounts.models import User
from django.utils import timezone


class Medecin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    specialite = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True)

    # 🔥 EXPERIENCE (AJOUT PRO SAFE)
    experience = models.IntegerField(
        null=True,
        blank=True,
        help_text="Années d'expérience"
    )

    numero_ordre = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True
    )

    disponible = models.BooleanField(default=True)

    date_creation = models.DateTimeField(
        default=timezone.now,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"Dr {self.user.username} - {self.specialite}"