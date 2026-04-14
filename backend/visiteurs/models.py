from django.db import models

class Visiteur(models.Model):
    nom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)

    def __str__(self):
        return self.nom
    
#historique
class JournalVisite(models.Model):
    visiteur = models.ForeignKey(Visiteur, on_delete=models.CASCADE)
    date_entree = models.DateTimeField(auto_now_add=True)
    date_sortie = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Visite {self.id}"