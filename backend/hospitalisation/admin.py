from django.contrib import admin
from .models import Hospitalisation, Chambre

admin.site.register(Hospitalisation)
admin.site.register(Chambre)