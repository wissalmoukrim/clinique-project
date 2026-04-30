from django.http import JsonResponse
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, log_security_event, optional_bool, optional_int, optional_string, parse_json_body, require_fields, require_int, require_string
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
            log_security_event(request.user, "forbidden_access", f"forbidden access to {request.path} with role {request.user.role}", request)
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
        user_id = require_int(data, "user_id")
        specialite = require_string(data, "specialite", 100)
        telephone = optional_string(data, "telephone", 20)
        numero_ordre = optional_string(data, "numero_ordre", 50) or None
        experience = optional_int(data, "experience")
        disponible = optional_bool(data, "disponible", True)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return json_error("User not found", 404)

    if user.role != "medecin":
        return json_error("User must have medecin role", 400)
    if Medecin.objects.filter(user=user).exists():
        return json_error("Medecin profile already exists", 400)

    medecin = Medecin.objects.create(
        user=user,
        specialite=specialite,
        telephone=telephone,
        numero_ordre=numero_ordre,
        disponible=disponible,
        experience=experience,
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
    log_action(request.user, "sensitive_access", "medecins.Medecin", medecin.id, "medecin profile access", request)
    return JsonResponse(serialize_medecin(medecin))
