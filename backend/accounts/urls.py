from django.urls import path
from .views import login_view, logout_view, register_view, CustomLoginView

urlpatterns = [
    # 🔐 Session (legacy)
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),

    # 🔥 JWT (principal pour React)
    path('jwt/login/', CustomLoginView.as_view(), name='jwt_login'),
]