from django.urls import path
from .views import ambulance_list, create_mission, mission_list, terminer_mission

urlpatterns = [
    path('', ambulance_list),
    path('missions/', mission_list),
    path('mission/create/', create_mission),
    path('mission/<int:id>/terminer/', terminer_mission),
]
