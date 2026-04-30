import json
from datetime import timedelta

from django.core.exceptions import SuspiciousOperation
from django.http import JsonResponse
from django.utils import timezone

from .models import AuditLog

SENSITIVE_INPUT_MARKERS = ("<", ">", "javascript:", "onerror=", "onload=", "<script")


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def log_action(user, action, resource="", object_id="", details="", request=None):
    return AuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        action=action,
        resource=resource or "",
        resource_id=str(object_id or ""),
        object_id=str(object_id or ""),
        details=details or "",
        ip_address=get_client_ip(request) if request else None,
    )


def log_security_event(user, action, details, request=None, resource="security"):
    log = log_action(user, action, resource, "", details, request)
    if action in {"login_failed", "forbidden_access"}:
        window_start = timezone.now() - timedelta(minutes=10)
        ip_address = get_client_ip(request) if request else None
        recent_events = AuditLog.objects.filter(
            action=action,
            timestamp__gte=window_start,
        )
        if user and getattr(user, "is_authenticated", False):
            recent_events = recent_events.filter(user=user)
        elif ip_address:
            recent_events = recent_events.filter(ip_address=ip_address)

        if recent_events.count() >= 3:
            log_action(
                user,
                "security_alert",
                resource,
                "",
                f"Repeated {action}: {details}",
                request,
            )
    return log


def clean_text(value, max_length=255, field_name="field"):
    if value is None:
        return ""
    value = str(value).strip()
    lowered = value.lower()
    if any(marker in lowered for marker in SENSITIVE_INPUT_MARKERS):
        raise SuspiciousOperation(f"Invalid characters in {field_name}")
    if len(value) > max_length:
        raise SuspiciousOperation(f"{field_name} is too long")
    return value


def require_string(data, field_name, max_length=255):
    value = data.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise SuspiciousOperation("Invalid input")
    return clean_text(value, max_length, field_name)


def optional_string(data, field_name, max_length=255):
    value = data.get(field_name)
    if value in (None, ""):
        return ""
    if not isinstance(value, str):
        raise SuspiciousOperation("Invalid input")
    return clean_text(value, max_length, field_name)


def require_int(data, field_name):
    value = data.get(field_name)
    if isinstance(value, bool):
        raise SuspiciousOperation("Invalid input")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise SuspiciousOperation("Invalid input")


def optional_int(data, field_name):
    value = data.get(field_name)
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise SuspiciousOperation("Invalid input")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise SuspiciousOperation("Invalid input")


def optional_bool(data, field_name, default=False):
    value = data.get(field_name, default)
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return default
    raise SuspiciousOperation("Invalid input")


def parse_json_body(request):
    if not request.body:
        return {}
    try:
        data = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def json_error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def require_fields(data, fields):
    return [field for field in fields if data.get(field) in (None, "")]
