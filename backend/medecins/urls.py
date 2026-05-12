from django.urls import path
from .views import medecin_list, create_medecin, my_profile, update_medecin, delete_medecin

urlpatterns = [
    path('', medecin_list, name="medecin_list"),
    path('create/', create_medecin, name="create_medecin"),
    path('me/', my_profile, name="medecin_profile"),
    path('<int:medecin_id>/', update_medecin, name="update_medecin"),
    path('delete/<int:medecin_id>/', delete_medecin, name="delete_medecin"),
]
