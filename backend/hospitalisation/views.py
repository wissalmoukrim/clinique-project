from django.core.exceptions import SuspiciousOperation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from consultations.models import Consultation
from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, log_security_event, optional_string, parse_json_body, require_fields, require_int, require_string
from .models import Chambre, Hospitalisation


def serialize_hospitalisation(hosp):
    patient_name = hosp.patient.user.get_full_name().strip() or hosp.patient.user.username
    return {
        "id": hosp.id,
        "patient": hosp.patient.user.username,
        "patient_id": hosp.patient_id,
        "patient_full_name": patient_name,
        "patient_display": patient_name,
        "chambre": hosp.chambre.numero if hosp.chambre else None,
        "date_entree": str(hosp.date_entree),
        "date_sortie": str(hosp.date_sortie) if hosp.date_sortie else None,
        "statut": hosp.statut,
        "motif": hosp.motif,
        "observations": hosp.observations,
        "temperature": hosp.temperature,
        "tension": hosp.tension,
        "frequence_cardiaque": hosp.frequence_cardiaque,
    }


@csrf_exempt
def hospitalisation_list(request):
    if not request.user.is_authenticated:
        return json_error("Unauthorized", 401)
    if request.method == "POST":
        return create_hospitalisation(request)
    if request.method != "GET":
        return json_error("Method not allowed", 405)

    role = request.user.role
    hosp = Hospitalisation.objects.select_related("patient__user", "chambre", "consultation__medecin__user")

    if role in ["admin", "secretaire", "infirmier"]:
        pass
    elif role == "medecin":
        hosp = hosp.filter(consultation__medecin__user=request.user)
    elif role == "patient":
        hosp = hosp.filter(patient__user=request.user)
    else:
        log_security_event(request.user, "forbidden_access", f"forbidden access to {request.path} with role {role}", request)
        return json_error("Forbidden", 403)

    log_action(request.user, "sensitive_access", "hospitalisation.Hospitalisation", "", "hospitalisation list access", request)
    return JsonResponse([serialize_hospitalisation(h) for h in hosp], safe=False)


@csrf_exempt
@method_required("POST")
@require_roles("medecin")
def create_hospitalisation(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["consultation_id", "chambre_id", "date_entree", "motif"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        consultation_id = require_int(data, "consultation_id")
        chambre_id = require_int(data, "chambre_id")
        date_entree = require_string(data, "date_entree", 20)
        motif = require_string(data, "motif", 255)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    try:
        consultation = Consultation.objects.select_related("patient", "medecin__user").get(id=consultation_id)
    except Consultation.DoesNotExist:
        return json_error("Consultation not found", 404)

    if request.user.role == "medecin" and consultation.medecin.user_id != request.user.id:
        log_security_event(request.user, "forbidden_access", f"forbidden hospitalisation create for consultation {consultation.id}", request)
        return json_error("Forbidden", 403)

    try:
        chambre = Chambre.objects.get(id=chambre_id)
    except Chambre.DoesNotExist:
        return json_error("Chambre not found", 404)

    if not chambre.disponible:
        return json_error("Chambre not available", 400)
    if Hospitalisation.objects.filter(consultation=consultation).exists():
        return json_error("Hospitalisation already exists for this consultation", 400)

    hosp = Hospitalisation.objects.create(
        patient=consultation.patient,
        consultation=consultation,
        chambre=chambre,
        date_entree=date_entree,
        motif=motif,
    )
    chambre.disponible = False
    chambre.save(update_fields=["disponible"])
    log_action(request.user, "create", "hospitalisation.Hospitalisation", hosp.id, request=request)
    return JsonResponse(serialize_hospitalisation(hosp), status=201)


@csrf_exempt
@method_required("POST")
@require_roles("admin", "medecin")
def sortie_patient(request, id):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    if not data.get("date_sortie"):
        return json_error("Missing fields: date_sortie", 400)

    try:
        date_sortie = require_string(data, "date_sortie", 20)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    try:
        hosp = Hospitalisation.objects.select_related("chambre", "consultation__medecin__user").get(id=id)
    except Hospitalisation.DoesNotExist:
        return json_error("Hospitalisation not found", 404)

    if request.user.role == "medecin" and hosp.consultation and hosp.consultation.medecin.user_id != request.user.id:
        log_security_event(request.user, "forbidden_access", f"forbidden hospitalisation sortie {id}", request)
        return json_error("Forbidden", 403)

    if hosp.statut == "termine":
        return json_error("Hospitalisation already completed", 400)

    hosp.date_sortie = date_sortie
    hosp.statut = "termine"
    hosp.save(update_fields=["date_sortie", "statut"])

    if hosp.chambre:
        hosp.chambre.disponible = True
        hosp.chambre.save(update_fields=["disponible"])

    log_action(request.user, "update", "hospitalisation.Hospitalisation", hosp.id, "sortie", request)
    return JsonResponse(serialize_hospitalisation(hosp))


@csrf_exempt
@method_required("PUT", "PATCH")
@require_roles("admin", "infirmier")
def update_monitoring(request, id):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    try:
        hosp = Hospitalisation.objects.select_related("patient__user", "chambre").get(id=id)
    except Hospitalisation.DoesNotExist:
        return json_error("Hospitalisation not found", 404)

    try:
        if "observations" in data:
            hosp.observations = optional_string(data, "observations", 4000)
        if "temperature" in data:
            hosp.temperature = optional_string(data, "temperature", 20)
        if "tension" in data:
            hosp.tension = optional_string(data, "tension", 20)
        if "frequence_cardiaque" in data:
            hosp.frequence_cardiaque = optional_string(data, "frequence_cardiaque", 20)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    hosp.save(update_fields=["observations", "temperature", "tension", "frequence_cardiaque"])
    log_action(request.user, "update", "hospitalisation.Hospitalisation", hosp.id, "nurse monitoring update", request)
    return JsonResponse(serialize_hospitalisation(hosp))
