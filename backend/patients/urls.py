from django.urls import path
from .views import patient_list, create_patient, my_profile

urlpatterns = [
    path('', patient_list),
    path('create/', create_patient),
    path('me/', my_profile),
]