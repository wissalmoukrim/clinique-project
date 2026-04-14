from django.contrib import admin
from .models import Consultation, Ordonnance, Medicament

admin.site.register(Consultation)
admin.site.register(Ordonnance)
admin.site.register(Medicament)