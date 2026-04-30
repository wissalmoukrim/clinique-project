from django.urls import path

from .views import chatbot_view, security_dashboard

urlpatterns = [
    path("chatbot/", chatbot_view, name="chatbot"),
    path("security/", security_dashboard, name="security_dashboard"),
]
