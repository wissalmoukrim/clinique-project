from django.contrib import admin
from .models import Facture, Paiement

admin.site.register(Facture)
admin.site.register(Paiement)