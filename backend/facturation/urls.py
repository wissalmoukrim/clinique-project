from django.urls import path
from .views import facture_list, create_facture, payer_facture

urlpatterns = [
    path('', facture_list),
    path('create/', create_facture),
    path('<int:id>/payer/', payer_facture),
]