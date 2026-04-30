from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, parse_json_body, require_fields
from .models import Personnel

PERSONNEL_ROLES = {"secretaire", "infirmier", "comptable", "securite", "chauffeur"}


def serialize_personnel(personnel):
    return {
        "id": personnel.id,
        "user_id": personnel.user_id,
        "username": personnel.user.username,
        "role": personnel.user.role,
        "fonction": personnel.fonction,
        "telephone": personnel.telephone,
        "adresse": personnel.adresse,
        "actif": personnel.actif,
    }


@csrf_exempt
@require_roles("admin")
def personnel_list(request):
    if request.method == "GET":
        personnels = Personnel.objects.select_related("user").all()
        return JsonResponse([serialize_personnel(p) for p in personnels], safe=False)
    if request.method == "POST":
        return create_personnel(request)
    return json_error("Method not allowed", 405)


@csrf_exempt
@method_required("POST")
@require_roles("admin")
def create_personnel(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["user_id"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        user = User.objects.get(id=data["user_id"])
    except User.DoesNotExist:
        return json_error("User not found", 404)

    if user.role not in PERSONNEL_ROLES:
        return json_error("User role is not a personnel role", 400)
    if Personnel.objects.filter(user=user).exists():
        return json_error("Personnel profile already exists", 400)

    personnel = Personnel.objects.create(
        user=user,
        fonction=user.role,
        telephone=data.get("telephone", ""),
        adresse=data.get("adresse", ""),
    )
    log_action(request.user, "create", "personnel.Personnel", personnel.id, request=request)
    return JsonResponse(serialize_personnel(personnel), status=201)
