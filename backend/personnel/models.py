from django.db import models
from accounts.models import User

class Personnel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fonction = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20)
    adresse = models.TextField()
    date_embauche = models.DateField()

    def __str__(self):
        return self.user.username