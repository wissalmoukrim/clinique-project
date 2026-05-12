from django.urls import path
from .views import hospitalisation_list, create_hospitalisation, sortie_patient, update_monitoring

urlpatterns = [
    path('', hospitalisation_list),
    path('create/', create_hospitalisation),
    path('<int:id>/monitoring/', update_monitoring),
    path('<int:id>/sortie/', sortie_patient),
]
