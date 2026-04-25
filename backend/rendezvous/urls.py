from django.urls import path
from .views import rendezvous_list, create_rdv, update_rdv_status

urlpatterns = [
    path('', rendezvous_list),
    path('create/', create_rdv),
    path('<int:id>/status/', update_rdv_status),
]