from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from accounts.models import User
from .models import AuditLog
from .chatbot import public_chatbot_response
from .permissions import ALL_ROLES, method_required, require_roles
from .utils import clean_text, log_action, parse_json_body, json_error


@csrf_exempt
@method_required("POST")
@require_roles(*ALL_ROLES)
def chatbot_view(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    try:
        message = clean_text(data.get("message", ""), 500, "message")
    except SuspiciousOperation as exc:
        return json_error(str(exc), 400)

    return JsonResponse({"response": public_chatbot_response(message)})


def serialize_audit_log(log):
    return {
        "id": log.id,
        "user": log.user.username if log.user else "anonymous",
        "role": log.user.role if log.user else None,
        "action": log.action,
        "resource": log.resource,
        "resource_id": log.resource_id,
        "object_id": log.object_id,
        "details": log.details,
        "ip_address": log.ip_address,
        "timestamp": log.timestamp.isoformat(),
    }


@csrf_exempt
@method_required("GET")
@require_roles("admin")
def security_dashboard(request):
    logs = AuditLog.objects.select_related("user").order_by("-timestamp")[:100]
    failed_logins = AuditLog.objects.filter(action="login_failed").count()
    forbidden_access = AuditLog.objects.filter(action="forbidden_access").count()
    alerts = AuditLog.objects.filter(action="security_alert").count()
    locked_accounts = User.objects.filter(is_locked=True).count()
    active_users = User.objects.filter(is_active=True).count()

    log_action(request.user, "sensitive_access", "core.AuditLog", "", "security dashboard access", request)

    return JsonResponse({
        "summary": {
            "failed_logins": failed_logins,
            "forbidden_access": forbidden_access,
            "alerts": alerts,
            "locked_accounts": locked_accounts,
            "active_users": active_users,
        },
        "logs": [serialize_audit_log(log) for log in logs],
        "locked_users": [
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "login_attempts": user.login_attempts,
                "last_failed_login": user.last_failed_login.isoformat() if user.last_failed_login else None,
            }
            for user in User.objects.filter(is_locked=True).order_by("username")
        ],
    })
