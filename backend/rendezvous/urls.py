from django.urls import path
from .views import rendezvous_list, create_rdv, update_rdv_status

urlpatterns = [
    path('', rendezvous_list, name="rendezvous_list"),
    path('create/', create_rdv, name="create_rdv"),
    path('<int:id>/status/', update_rdv_status, name="update_rdv_status"),
    path('<int:id>/update-status/', update_rdv_status, name="update_rdv_status_v2"),
]
