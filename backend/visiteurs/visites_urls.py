from django.urls import path

from .views import create_visite_entree, sortie_visite, visite_list, visites_presentes


urlpatterns = [
    path("", visite_list),
    path("entree/", create_visite_entree),
    path("presents/", visites_presentes),
    path("<int:id>/sortie/", sortie_visite),
]
