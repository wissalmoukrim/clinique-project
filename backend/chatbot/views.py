from datetime import timedelta

from django.core.exceptions import SuspiciousOperation
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from core.chatbot import FORBIDDEN_TOPICS, public_chatbot_response
from core.models import AuditLog
from core.utils import clean_text, get_client_ip, log_action, log_security_event


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


class ChatbotRateThrottle(AnonRateThrottle):
    rate = "20/minute"


def is_suspicious_chatbot_message(message):
    text = (message or "").lower()
    return any(marker in text for marker in PROMPT_INJECTION_MARKERS) or any(topic in text for topic in FORBIDDEN_TOPICS)


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
@permission_classes([AllowAny])
@throttle_classes([ChatbotRateThrottle])
def chatbot_view(request):
    if is_chatbot_ip_rate_limited(request):
        log_security_event(None, "security_alert", "chatbot IP rate limit exceeded", request, resource="chatbot")
        return Response({"error": "Too many chatbot requests"}, status=429)

    try:
        message = clean_text(request.data.get("message", ""), 500, "message")
    except SuspiciousOperation as exc:
        log_security_event(None, "security_alert", f"chatbot rejected unsafe input: {exc}", request, resource="chatbot")
        return Response({"response": "Je peux repondre uniquement aux informations publiques de la clinique."}, status=400)

    if is_suspicious_chatbot_message(message):
        log_action(None, "chatbot_blocked", "chatbot", "", f"blocked query: {message[:120]}", request, status="warning")
        log_security_event(None, "security_alert", "suspicious chatbot request", request, resource="chatbot")
        return Response({"response": "Je ne peux pas acceder aux donnees internes, medicales, administratives ou aux identifiants."})

    response = public_chatbot_response(message)
    log_action(None, "chatbot_query", "chatbot", "", message[:200], request)
    return Response({"response": response})
