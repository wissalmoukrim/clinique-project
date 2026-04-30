from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, parse_json_body, require_fields
from .models import Medecin


def serialize_medecin(medecin):
    return {
        "id": medecin.id,
        "user_id": medecin.user_id,
        "username": medecin.user.username,
        "specialite": medecin.specialite,
        "telephone": medecin.telephone,
        "numero_ordre": medecin.numero_ordre,
        "disponible": medecin.disponible,
        "experience": medecin.experience,
    }


@csrf_exempt
def medecin_list(request):
    if request.method == "GET":
        if request.user.is_authenticated and request.user.role not in ["admin", "secretaire", "medecin", "patient"]:
            return json_error("Forbidden", 403)
        medecins = Medecin.objects.select_related("user").all()
        return JsonResponse([serialize_medecin(m) for m in medecins], safe=False)
    if request.method == "POST":
        return create_medecin(request)
    return json_error("Method not allowed", 405)


@csrf_exempt
@method_required("POST")
@require_roles("admin")
def create_medecin(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["user_id", "specialite"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        user = User.objects.get(id=data["user_id"])
    except User.DoesNotExist:
        return json_error("User not found", 404)

    if user.role != "medecin":
        return json_error("User must have medecin role", 400)
    if Medecin.objects.filter(user=user).exists():
        return json_error("Medecin profile already exists", 400)

    medecin = Medecin.objects.create(
        user=user,
        specialite=data["specialite"],
        telephone=data.get("telephone", ""),
        numero_ordre=data.get("numero_ordre") or None,
        disponible=bool(data.get("disponible", True)),
        experience=data.get("experience"),
    )
    log_action(request.user, "create", "medecins.Medecin", medecin.id, request=request)
    return JsonResponse(serialize_medecin(medecin), status=201)


@csrf_exempt
@method_required("GET")
@require_roles("medecin")
def my_profile(request):
    try:
        medecin = Medecin.objects.select_related("user").get(user=request.user)
    except Medecin.DoesNotExist:
        return json_error("Medecin not found", 404)
    return JsonResponse(serialize_medecin(medecin))
