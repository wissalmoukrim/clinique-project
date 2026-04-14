from django.db import models
from accounts.models import User
from specialites.models import Specialite

class Medecin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    specialite = models.ForeignKey(Specialite, on_delete=models.CASCADE)
    experience = models.IntegerField()

    def __str__(self):
        return self.user.username