from django.urls import path
from .views import (
    CustomLoginView,
    admin_reset_password,
    change_password,
    employee_collection,
    employee_detail,
    login_view,
    logout_view,
    register_view,
    user_list,
)

urlpatterns = [
    # 🔐 Session (legacy)
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('users/', user_list, name='user_list'),
    path('employees/', employee_collection, name='employee_collection'),
    path('employees/<int:user_id>/', employee_detail, name='employee_detail'),
    path('password/change/', change_password, name='change_password'),
    path('password/reset/', admin_reset_password, name='admin_reset_password'),

    # 🔥 JWT (principal pour React)
    path('jwt/login/', CustomLoginView.as_view(), name='jwt_login'),
]
