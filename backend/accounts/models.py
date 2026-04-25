from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('medecin', 'Medecin'),
        ('patient', 'Patient'),
        ('secretaire', 'Secretaire'),
        ('infirmier', 'Infirmier'),
        ('comptable', 'Comptable'),
        ('securite', 'Securite'),
        ('chauffeur', 'Chauffeur'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')

    # 🔐 sécurité login
    login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.role})"