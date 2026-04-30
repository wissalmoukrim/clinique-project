from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import SuspiciousOperation
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import TokenObtainPairView

from core.models import AuditLog
from core.permissions import ALL_ROLES, method_required, require_roles
from core.utils import clean_text, get_client_ip, json_error, log_action, log_security_event, parse_json_body, require_fields
from .models import User
from .serializers import CustomTokenSerializer

MAX_LOGIN_ATTEMPTS = 5
MAX_LOGIN_ATTEMPTS_PER_IP = 10
IP_RATE_LIMIT_WINDOW_MINUTES = 15


def is_ip_rate_limited(request):
    ip_address = request.META.get("REMOTE_ADDR") or get_client_ip(request)
    if not ip_address:
        return False

    window_start = timezone.now() - timedelta(minutes=IP_RATE_LIMIT_WINDOW_MINUTES)
    attempts = AuditLog.objects.filter(
        action="login_failed",
        ip_address=ip_address,
        timestamp__gte=window_start,
    ).count()
    return attempts >= MAX_LOGIN_ATTEMPTS_PER_IP


@csrf_exempt
@method_required("POST")
def login_view(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["username", "password"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    if not isinstance(data.get("username"), str) or not isinstance(data.get("password"), str):
        return json_error("Invalid input", 400)

    if is_ip_rate_limited(request):
        log_security_event(None, "security_alert", "login blocked by IP rate limit", request)
        return json_error("Too many login attempts from this IP", 429)

    try:
        username = clean_text(data["username"], 150, "username")
    except SuspiciousOperation as exc:
        return json_error(str(exc), 400)
    password = data["password"]
    user = User.objects.filter(username=username).first()

    if not user:
        log_security_event(None, "login_failed", f"unknown username {username}", request)
        return json_error("Invalid credentials", 401)

    if user.is_locked:
        log_security_event(user, "login_failed", "locked account login attempt", request)
        return json_error("Account locked", 403)

    user_auth = authenticate(request, username=username, password=password)
    if user_auth is not None:
        login(request, user_auth)
        user_auth.login_attempts = 0
        user_auth.last_failed_login = None
        user_auth.save(update_fields=["login_attempts", "last_failed_login"])
        log_action(user_auth, "login_success", "accounts.User", user_auth.id, "session login", request)

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
    detail = "account locked after failed login" if user.is_locked else "failed login"
    log_security_event(user, "login_failed", detail, request)

    return json_error("Invalid credentials", 401)


class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return json_error("Missing credentials", 400)

        if not isinstance(username, str) or not isinstance(password, str):
            return json_error("Invalid input", 400)

        if is_ip_rate_limited(request):
            log_security_event(None, "security_alert", "jwt login blocked by IP rate limit", request)
            return json_error("Too many login attempts from this IP", 429)

        try:
            username = clean_text(username, 150, "username")
        except SuspiciousOperation as exc:
            return json_error(str(exc), 400)

        user = User.objects.filter(username=username).first()
        if not user:
            log_security_event(None, "login_failed", f"unknown username {username}", request)
            return json_error("Invalid credentials", 401)

        if user.is_locked:
            log_security_event(user, "login_failed", "locked account login attempt", request)
            return json_error("Account locked", 403)

        user_auth = authenticate(request, username=username, password=password)
        if not user_auth:
            user.login_attempts += 1
            user.last_failed_login = timezone.now()
            if user.login_attempts >= MAX_LOGIN_ATTEMPTS:
                user.is_locked = True
            user.save(update_fields=["login_attempts", "last_failed_login", "is_locked"])
            detail = "account locked after failed jwt login" if user.is_locked else "failed jwt login"
            log_security_event(user, "login_failed", detail, request)
            return json_error("Invalid credentials", 401)

        user.login_attempts = 0
        user.last_failed_login = None
        user.save(update_fields=["login_attempts", "last_failed_login"])
        log_action(user, "login_success", "accounts.User", user.id, "jwt login", request)

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

    if not isinstance(data.get("username"), str) or not isinstance(data.get("password"), str):
        return json_error("Invalid input", 400)

    try:
        username = clean_text(data["username"], 150, "username")
    except SuspiciousOperation as exc:
        return json_error(str(exc), 400)
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
