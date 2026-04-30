from django.urls import path
from .views import medecin_list, create_medecin, my_profile

urlpatterns = [
    path('', medecin_list, name="medecin_list"),
    path('create/', create_medecin, name="create_medecin"),
    path('me/', my_profile, name="medecin_profile"),
]
