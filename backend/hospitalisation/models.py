from django.db import models


# ================= CHAMBRE =================
class Chambre(models.Model):
    numero = models.CharField(max_length=10)
    type = models.CharField(max_length=50)  # simple, double, VIP
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"Chambre {self.numero} ({self.type})"


# ================= HOSPITALISATION =================
class Hospitalisation(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE)

    consultation = models.OneToOneField(
        "consultations.Consultation",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    chambre = models.ForeignKey(Chambre, on_delete=models.SET_NULL, null=True)

    date_entree = models.DateField()
    date_sortie = models.DateField(null=True, blank=True)

    motif = models.TextField(default="")

    STATUT_CHOICES = [
        ('en cours', 'En cours'),
        ('sorti', 'Sorti'),
    ]

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='en cours'
    )

    def __str__(self):
        return f"{self.patient.user.username} - {self.statut}"
