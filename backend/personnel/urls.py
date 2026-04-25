from django.urls import path
from .views import personnel_list, create_personnel

urlpatterns = [
    path('', personnel_list),
    path('create/', create_personnel),
]