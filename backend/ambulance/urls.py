from django.urls import path
from .views import ambulance_list, create_mission, terminer_mission

urlpatterns = [
    path('', ambulance_list),
    path('mission/create/', create_mission),
    path('mission/<int:id>/terminer/', terminer_mission),
]