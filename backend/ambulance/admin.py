from django.contrib import admin
from .models import Ambulance, Chauffeur, MissionAmbulance

admin.site.register(Ambulance)
admin.site.register(Chauffeur)
admin.site.register(MissionAmbulance)