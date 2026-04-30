from django.db import models


# ================= CONSULTATION =================
class Consultation(models.Model):
    patient = models.ForeignKey("patients.Patient", on_delete=models.CASCADE)
    medecin = models.ForeignKey("medecins.Medecin", on_delete=models.CASCADE)
    rendezvous = models.OneToOneField("rendezvous.RendezVous", on_delete=models.CASCADE)

    date = models.DateField(auto_now_add=True)

    diagnostic = models.TextField()
    traitement = models.TextField(blank=True)

    def __str__(self):
        return f"Consultation {self.patient.user.username} - {self.medecin.user.username}"


# ================= ORDONNANCE =================
class Ordonnance(models.Model):
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE)

    date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Ordonnance {self.consultation.id}"


# ================= MEDICAMENT =================
class Medicament(models.Model):
    ordonnance = models.ForeignKey(Ordonnance, on_delete=models.CASCADE, related_name="medicaments")

    nom = models.CharField(max_length=100)
    dosage = models.CharField(max_length=100)
    frequence = models.CharField(max_length=100)
    duree = models.CharField(max_length=100)

    def __str__(self):
        return self.nom
