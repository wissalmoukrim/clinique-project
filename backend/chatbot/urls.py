from django.urls import path
from .views import chatbot_view, public_chatbot_view

urlpatterns = [
    path('public/ask/', public_chatbot_view, name="public_chatbot_view"),
    path('ask/', chatbot_view, name="chatbot_view"),
]
