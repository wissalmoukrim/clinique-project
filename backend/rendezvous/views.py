from django.http import JsonResponse
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_exempt

from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, log_security_event, parse_json_body, require_fields, require_int, require_string
from medecins.models import Medecin
from patients.models import Patient
from .models import RendezVous

ALLOWED_STATUTS = {choice[0] for choice in RendezVous.STATUT_CHOICES}
STATUS_ALIASES = {
    "valide": RendezVous.STATUT_CHOICES[1][0],
    "validé": RendezVous.STATUT_CHOICES[1][0],
    "confirme": RendezVous.STATUT_CHOICES[1][0],
    "confirmé": RendezVous.STATUT_CHOICES[1][0],
    "annule": RendezVous.STATUT_CHOICES[2][0],
    "annulé": RendezVous.STATUT_CHOICES[2][0],
    "en_attente": RendezVous.STATUT_CHOICES[0][0],
}


def serialize_rdv(rdv):
    return {
        "id": rdv.id,
        "patient_id": rdv.patient_id,
        "patient": rdv.patient.user.username,
        "medecin_id": rdv.medecin_id,
        "medecin": rdv.medecin.user.username,
        "date": str(rdv.date),
        "heure": str(rdv.heure),
        "statut": rdv.statut,
    }


@csrf_exempt
def rendezvous_list(request):
    if not request.user.is_authenticated:
        return json_error("Unauthorized", 401)

    if request.method == "POST":
        return create_rdv(request)
    if request.method != "GET":
        return json_error("Method not allowed", 405)

    role = request.user.role
    rdvs = RendezVous.objects.select_related("patient__user", "medecin__user")

    if role in ["admin", "secretaire"]:
        pass
    elif role == "medecin":
        rdvs = rdvs.filter(medecin__user=request.user)
    elif role == "patient":
        rdvs = rdvs.filter(patient__user=request.user)
    else:
        log_security_event(request.user, "forbidden_access", f"forbidden access to {request.path} with role {role}", request)
        return json_error("Forbidden", 403)

    log_action(request.user, "sensitive_access", "rendezvous.RendezVous", "", "rendezvous list access", request)
    return JsonResponse([serialize_rdv(r) for r in rdvs], safe=False)


@csrf_exempt
@method_required("POST")
@require_roles("admin", "secretaire", "patient")
def create_rdv(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["medecin_id", "date", "heure"])
    if request.user.role in ["admin", "secretaire"] and not data.get("patient_id"):
        missing.append("patient_id")
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        medecin_id = require_int(data, "medecin_id")
        patient_id = require_int(data, "patient_id") if request.user.role in ["admin", "secretaire"] else None
        date = require_string(data, "date", 20)
        heure = require_string(data, "heure", 20)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    try:
        medecin = Medecin.objects.get(id=medecin_id)
    except Medecin.DoesNotExist:
        return json_error("Medecin not found", 404)

    try:
        if request.user.role == "patient":
            patient = Patient.objects.get(user=request.user)
        else:
            patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return json_error("Patient not found", 404)

    rdv = RendezVous.objects.create(
        patient=patient,
        medecin=medecin,
        date=date,
        heure=heure,
    )
    log_action(request.user, "create", "rendezvous.RendezVous", rdv.id, request=request)
    return JsonResponse(serialize_rdv(rdv), status=201)


@csrf_exempt
@method_required("POST")
@require_roles("admin", "secretaire", "medecin")
def update_rdv_status(request, id):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    try:
        raw_statut = require_string(data, "statut", 30)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    statut = STATUS_ALIASES.get(raw_statut, raw_statut)
    if statut not in ALLOWED_STATUTS:
        return json_error("Invalid statut", 400)

    try:
        rdv = RendezVous.objects.select_related("medecin__user").get(id=id)
    except RendezVous.DoesNotExist:
        return json_error("Rendez-vous not found", 404)

    if request.user.role == "medecin" and rdv.medecin.user_id != request.user.id:
        log_security_event(request.user, "forbidden_access", f"forbidden rendezvous status update {id}", request)
        return json_error("Forbidden", 403)

    rdv.statut = statut
    rdv.save(update_fields=["statut"])
    log_action(request.user, "update", "rendezvous.RendezVous", rdv.id, request=request)
    return JsonResponse(serialize_rdv(rdv))
