from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import SuspiciousOperation
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import TokenObtainPairView

from core.models import AuditLog
from core.permissions import ALL_ROLES, method_required, require_roles
from core.utils import clean_text, get_client_ip, json_error, log_action, log_security_event, optional_bool, optional_int, optional_string, parse_json_body, require_fields, require_string
from medecins.models import Medecin
from personnel.models import Personnel
from .models import User
from .serializers import CustomTokenSerializer

MAX_LOGIN_ATTEMPTS = 5
MAX_LOGIN_ATTEMPTS_PER_IP = 10
IP_RATE_LIMIT_WINDOW_MINUTES = 15
EMPLOYEE_ROLES = {"medecin", "secretaire", "infirmier", "comptable", "securite", "chauffeur"}
PERSONNEL_ROLES = {"secretaire", "infirmier", "comptable", "securite", "chauffeur"}


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
    if not is_strong_password(password):
        return json_error(password_policy_message(), 400)

    if User.objects.filter(username=username).exists():
        return json_error("User already exists", 400)

    user = User.objects.create_user(username=username, password=password, role=role)
    log_action(request.user, "register", "accounts.User", user.id, request=request)

    return JsonResponse({
        "message": "User created",
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }, status=201)


def is_strong_password(password):
    if not isinstance(password, str):
        return False
    try:
        validate_password(password)
    except Exception:
        return False
    return True


def password_policy_message():
    return "Password must contain at least 8 characters, uppercase, lowercase, number and special character"


def serialize_employee(user):
    medecin = getattr(user, "medecin", None)
    personnel = getattr(user, "personnel", None)
    phone = ""
    active = user.is_active
    if medecin:
        phone = medecin.telephone
    if personnel:
        phone = personnel.telephone
        active = active and personnel.actif

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.get_full_name().strip() or user.username,
        "role": user.role,
        "telephone": phone,
        "is_active": user.is_active,
        "actif": active,
        "is_locked": user.is_locked,
        "date_joined": user.date_joined.isoformat() if user.date_joined else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "specialite": medecin.specialite if medecin else "",
        "experience": medecin.experience if medecin else "",
    }


def sync_employee_profile(user, data):
    telephone = optional_string(data, "telephone", 20)
    if user.role == "medecin":
      specialite = optional_string(data, "specialite", 100)
      experience = optional_int(data, "experience")
      medecin, _ = Medecin.objects.get_or_create(user=user, defaults={"specialite": specialite or "Medecine generale"})
      if specialite:
          medecin.specialite = specialite
      medecin.telephone = telephone
      medecin.experience = experience
      medecin.save()
    elif user.role in PERSONNEL_ROLES:
      personnel, _ = Personnel.objects.get_or_create(user=user, defaults={"fonction": user.role})
      personnel.fonction = user.role
      personnel.telephone = telephone
      if "actif" in data:
          personnel.actif = optional_bool(data, "actif", personnel.actif)
      personnel.save()


@csrf_exempt
@method_required("GET")
@require_roles("admin")
def user_list(request):
    users = User.objects.select_related("medecin", "personnel").order_by("role", "username")
    return JsonResponse([serialize_employee(user) for user in users], safe=False)


@csrf_exempt
@require_roles("admin")
def employee_collection(request):
    if request.method == "GET":
        users = User.objects.select_related("medecin", "personnel").filter(role__in=EMPLOYEE_ROLES).order_by("role", "username")
        return JsonResponse([serialize_employee(user) for user in users], safe=False)
    if request.method == "POST":
        return create_employee(request)
    return json_error("Method not allowed", 405)


@csrf_exempt
@method_required("POST")
@require_roles("admin")
def create_employee(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["first_name", "last_name", "username", "email", "role", "password"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        first_name = require_string(data, "first_name", 100)
        last_name = require_string(data, "last_name", 100)
        username = require_string(data, "username", 150)
        email = require_string(data, "email", 150).lower()
        role = require_string(data, "role", 20)
        password = data.get("password")
        validate_email(email)
    except Exception:
        return json_error("Invalid input", 400)

    if role not in EMPLOYEE_ROLES:
        return json_error("Invalid employee role", 400)
    if not is_strong_password(password):
        return json_error(password_policy_message(), 400)
    if User.objects.filter(username=username).exists():
        return json_error("Username already exists", 400)
    if User.objects.filter(email=email).exists():
        return json_error("Email already exists", 400)
    if role == "medecin" and not data.get("specialite"):
        return json_error("Missing fields: specialite", 400)

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role,
                first_name=first_name,
                last_name=last_name,
            )
            sync_employee_profile(user, data)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    log_action(request.user, "register", "accounts.User", user.id, "admin employee create", request)
    return JsonResponse(serialize_employee(user), status=201)


@csrf_exempt
@method_required("PUT", "PATCH", "DELETE")
@require_roles("admin")
def employee_detail(request, user_id):
    try:
        user = User.objects.select_related("medecin", "personnel").get(id=user_id, role__in=EMPLOYEE_ROLES)
    except User.DoesNotExist:
        return json_error("Employee not found", 404)

    if request.method == "DELETE":
        if user.id == request.user.id:
            return json_error("You cannot delete your own account", 400)
        deleted_id = user.id
        user.delete()
        log_action(request.user, "delete", "accounts.User", deleted_id, "admin employee delete", request)
        return JsonResponse({"message": "Employee deleted"})

    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    try:
        if "first_name" in data:
            user.first_name = optional_string(data, "first_name", 100)
        if "last_name" in data:
            user.last_name = optional_string(data, "last_name", 100)
        if "username" in data:
            username = require_string(data, "username", 150)
            if User.objects.exclude(id=user.id).filter(username=username).exists():
                return json_error("Username already exists", 400)
            user.username = username
        if "email" in data:
            email = require_string(data, "email", 150).lower()
            validate_email(email)
            if User.objects.exclude(id=user.id).filter(email=email).exists():
                return json_error("Email already exists", 400)
            user.email = email
        if "role" in data:
            role = require_string(data, "role", 20)
            if role not in EMPLOYEE_ROLES:
                return json_error("Invalid employee role", 400)
            user.role = role
        if "is_active" in data:
            user.is_active = optional_bool(data, "is_active", user.is_active)
        user.save()
        sync_employee_profile(user, data)
    except (SuspiciousOperation, Exception):
        return json_error("Invalid input", 400)

    log_action(request.user, "update", "accounts.User", user.id, "admin employee update", request)
    return JsonResponse(serialize_employee(User.objects.select_related("medecin", "personnel").get(id=user.id)))


@csrf_exempt
@method_required("POST")
@require_roles(*ALL_ROLES)
def change_password(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["current_password", "new_password"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    current_password = data.get("current_password")
    new_password = data.get("new_password")
    if not isinstance(current_password, str) or not isinstance(new_password, str):
        return json_error("Invalid input", 400)
    if not request.user.check_password(current_password):
        log_security_event(request.user, "security_alert", "password change failed: invalid current password", request)
        return json_error("Invalid current password", 400)
    if not is_strong_password(new_password):
        return json_error(password_policy_message(), 400)

    request.user.set_password(new_password)
    request.user.login_attempts = 0
    request.user.is_locked = False
    request.user.last_failed_login = None
    request.user.save(update_fields=["password", "login_attempts", "is_locked", "last_failed_login"])
    log_action(request.user, "update", "accounts.User", request.user.id, "password changed", request)
    return JsonResponse({"message": "Password changed"})


@csrf_exempt
@method_required("POST")
@require_roles("admin")
def admin_reset_password(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["user_id"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        user_id = require_int(data, "user_id")
        user = User.objects.get(id=user_id)
    except (SuspiciousOperation, User.DoesNotExist):
        return json_error("User not found", 404)

    temporary_password = get_random_string(12) + "aA1!"
    user.set_password(temporary_password)
    user.login_attempts = 0
    user.is_locked = False
    user.last_failed_login = None
    user.save(update_fields=["password", "login_attempts", "is_locked", "last_failed_login"])
    log_action(request.user, "update", "accounts.User", user.id, "admin password reset", request)
    return JsonResponse({"message": "Password reset", "temporary_password": temporary_password})
