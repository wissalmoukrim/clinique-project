from django.urls import path
from .views import patient_list, create_patient, create_patient_account, my_profile, delete_patient, update_patient

urlpatterns = [
    path('', patient_list, name="patient_list"),
    path('create/', create_patient, name="create_patient"),
    path('create-account/', create_patient_account, name="create_patient_account"),
    path('me/', my_profile, name="my_profile"),
    path('<int:patient_id>/', update_patient, name="update_patient"),
    path('delete/<int:patient_id>/', delete_patient, name="delete_patient"),
]
