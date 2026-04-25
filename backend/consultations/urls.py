from django.urls import path
from .views import consultation_list, create_consultation

urlpatterns = [
    path('', consultation_list),
    path('create/', create_consultation),
]