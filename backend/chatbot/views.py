from datetime import timedelta

from django.core.exceptions import SuspiciousOperation
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from core.models import AuditLog
from core.utils import clean_text, get_client_ip, log_action, log_security_event


from .services import generate_patient_chatbot_response

from .serializers import ChatbotRequestSerializer, ChatbotResponseSerializer






PROMPT_INJECTION_MARKERS = {
    "ignore previous",
    "ignore instructions",
    "system prompt",
    "developer message",
    "admin password",
    "token",
    "jwt",
    "database",
    "sql",
    "credentials",
}


class ChatbotRateThrottle(UserRateThrottle):
    rate = "20/minute"


def is_suspicious_chatbot_message(message):
    text = (message or "").lower()
    return any(marker in text for marker in PROMPT_INJECTION_MARKERS)


def is_chatbot_ip_rate_limited(request):
    ip_address = get_client_ip(request)
    if not ip_address:
        return False
    window_start = timezone.now() - timedelta(minutes=5)
    return AuditLog.objects.filter(
        action__in=["chatbot_query", "chatbot_blocked"],
        ip_address=ip_address,
        timestamp__gte=window_start,
    ).count() >= 30


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([ChatbotRateThrottle])
def chatbot_view(request):
    if getattr(request.user, "role", None) != "patient":
        log_security_event(
            request.user,
            "forbidden_access",
            f"forbidden chatbot access with role {getattr(request.user, 'role', None)}",
            request,
            resource="chatbot",
        )
        return Response({"error": "Forbidden"}, status=403)

    if is_chatbot_ip_rate_limited(request):
        log_security_event(None, "security_alert", "chatbot IP rate limit exceeded", request, resource="chatbot")
        return Response({"error": "Too many chatbot requests"}, status=429)

    serializer = ChatbotRequestSerializer(data=request.data)
    if not serializer.is_valid():
        log_security_event(None, "security_alert", "chatbot rejected invalid payload", request, resource="chatbot")
        return Response({"response": "Je peux repondre uniquement aux informations publiques de la clinique."}, status=400)

    try:
        message = clean_text(serializer.validated_data.get("message", ""), 500, "message")
    except SuspiciousOperation as exc:
        log_security_event(None, "security_alert", f"chatbot rejected unsafe input: {exc}", request, resource="chatbot")
        return Response({"response": "Je peux repondre uniquement aux informations publiques de la clinique."}, status=400)

    if is_suspicious_chatbot_message(message):
        log_action(None, "chatbot_blocked", "chatbot", "", f"blocked query: {message[:120]}", request, status="warning")
        log_security_event(None, "security_alert", "suspicious chatbot request", request, resource="chatbot")
        payload = {"response": "Je ne peux pas acceder aux donnees internes, medicales, administratives ou aux identifiants."}
        return Response(ChatbotResponseSerializer(payload).data)
    

    response = generate_patient_chatbot_response(request.user, message)
    log_action(request.user, "chatbot_query", "chatbot", "", message[:200], request)
    return Response({"response": response})

   




