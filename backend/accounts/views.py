from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import TokenObtainPairView

from core.permissions import ALL_ROLES, method_required, require_roles
from core.utils import json_error, log_action, parse_json_body, require_fields
from .models import User
from .serializers import CustomTokenSerializer

MAX_LOGIN_ATTEMPTS = 5


@csrf_exempt
@method_required("POST")
def login_view(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["username", "password"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    username = data["username"]
    password = data["password"]
    user = User.objects.filter(username=username).first()

    if not user:
        return json_error("Invalid credentials", 401)

    if user.is_locked:
        return json_error("Account locked", 403)

    user_auth = authenticate(request, username=username, password=password)
    if user_auth is not None:
        login(request, user_auth)
        user_auth.login_attempts = 0
        user_auth.last_failed_login = None
        user_auth.save(update_fields=["login_attempts", "last_failed_login"])
        log_action(user_auth, "login", "accounts.User", user_auth.id, "session login", request)

        return JsonResponse({
            "message": "Login success",
            "username": user_auth.username,
            "role": user_auth.role,
        })

    user.login_attempts += 1
    user.last_failed_login = timezone.now()
    if user.login_attempts >= MAX_LOGIN_ATTEMPTS:
        user.is_locked = True
    user.save(update_fields=["login_attempts", "last_failed_login", "is_locked"])

    return json_error("Invalid credentials", 401)


class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return json_error("Missing credentials", 400)

        user = User.objects.filter(username=username).first()
        if not user:
            return json_error("Invalid credentials", 401)

        if user.is_locked:
            return json_error("Account locked", 403)

        user_auth = authenticate(request, username=username, password=password)
        if not user_auth:
            user.login_attempts += 1
            user.last_failed_login = timezone.now()
            if user.login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.is_locked = True
            user.save(update_fields=["login_attempts", "last_failed_login", "is_locked"])
            return json_error("Invalid credentials", 401)

        user.login_attempts = 0
        user.last_failed_login = None
        user.save(update_fields=["login_attempts", "last_failed_login"])
        log_action(user, "login", "accounts.User", user.id, "jwt login", request)

        return super().post(request, *args, **kwargs)


@csrf_exempt
@method_required("POST")
@require_roles(*ALL_ROLES)
def logout_view(request):
    log_action(request.user, "logout", "accounts.User", request.user.id, request=request)
    logout(request)
    return JsonResponse({"message": "Logout success"})


@csrf_exempt
@method_required("POST")
@require_roles("admin")
def register_view(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["username", "password"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    username = data["username"]
    password = data["password"]
    role = data.get("role", "patient")
    allowed_roles = {choice[0] for choice in User.ROLE_CHOICES}

    if role not in allowed_roles:
        return json_error("Invalid role", 400)

    if User.objects.filter(username=username).exists():
        return json_error("User already exists", 400)

    user = User.objects.create_user(username=username, password=password, role=role)
    log_action(request.user, "register", "accounts.User", user.id, request=request)

    return JsonResponse({
        "message": "User created",
        "username": user.username,
        "role": user.role,
    }, status=201)
