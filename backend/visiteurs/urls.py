from django.urls import path
from .views import visiteur_list, create_visiteur, entree_visiteur, sortie_visiteur

urlpatterns = [
    path('', visiteur_list),
    path('create/', create_visiteur),
    path('entree/', entree_visiteur),
    path('<int:id>/sortie/', sortie_visiteur),
]