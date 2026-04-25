from django.db import models
from accounts.models import User


# ================= PERSONNEL =================
class Personnel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # infos pro
    fonction = models.CharField(max_length=50)  # secretaire, infirmier, securite, comptable, chauffeur
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.CharField(max_length=255, blank=True)

    date_embauche = models.DateField(auto_now_add=True)

    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.fonction}"