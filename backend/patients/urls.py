from django.urls import path
from .views import patient_list, create_patient, my_profile, delete_patient

urlpatterns = [
    path('', patient_list, name="patient_list"),
    path('create/', create_patient, name="create_patient"),
    path('me/', my_profile, name="my_profile"),
    path('delete/<int:patient_id>/', delete_patient, name="delete_patient"),
]
