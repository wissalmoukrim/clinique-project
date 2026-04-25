from django.urls import path
from .views import medecin_list, create_medecin, my_medecin_profile

urlpatterns = [
    path('', medecin_list),
    path('create/', create_medecin),
    path('me/', my_medecin_profile),
]