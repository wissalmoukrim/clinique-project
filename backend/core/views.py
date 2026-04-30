from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from .chatbot import public_chatbot_response
from .permissions import ALL_ROLES, method_required, require_roles
from .utils import parse_json_body, json_error


@csrf_exempt
@method_required("POST")
@require_roles(*ALL_ROLES)
def chatbot_view(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    return JsonResponse({
        "response": public_chatbot_response(data.get("message", ""))
    })
