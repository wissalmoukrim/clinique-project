from django.db import models
from accounts.models import User

class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    telephone = models.CharField(max_length=20)
    adresse = models.TextField()

    def __str__(self):
        return self.user.username