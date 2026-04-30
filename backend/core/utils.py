import json

from django.http import JsonResponse

from .models import AuditLog


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
        object_id=str(object_id or ""),
        details=details or "",
        ip_address=get_client_ip(request) if request else None,
    )


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
