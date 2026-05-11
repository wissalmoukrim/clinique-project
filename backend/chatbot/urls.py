from django.urls import path
from .views import chatbot_view

urlpatterns = [
    path('ask/', chatbot_view),
]