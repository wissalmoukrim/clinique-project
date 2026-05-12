from django.urls import path
from .views import ambulance_list, create_mission, mission_list, start_mission, terminer_mission, update_ambulance, delete_ambulance

urlpatterns = [
    path('', ambulance_list),
    path('<int:ambulance_id>/', update_ambulance),
    path('<int:ambulance_id>/delete/', delete_ambulance),
    path('missions/', mission_list),
    path('mission/create/', create_mission),
    path('mission/<int:id>/start/', start_mission),
    path('mission/<int:id>/terminer/', terminer_mission),
]
