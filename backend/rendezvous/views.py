from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousOperation, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.utils.dateparse import parse_date, parse_time
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt

from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, log_security_event, optional_string, parse_json_body, require_fields, require_int, require_string
from medecins.models import Medecin
from patients.models import Patient
from .models import RendezVous

User = get_user_model()

ALLOWED_STATUTS = {choice[0] for choice in RendezVous.STATUT_CHOICES}
STATUS_ALIASES = {
    "en attente": "en_attente",
    "en_attente": "en_attente",
    "valide": "confirme",
    "validé": "confirme",
    "confirme": "confirme",
    "confirmé": "confirme",
    "annule": "annule",
    "annulé": "annule",
    "termine": "termine",
    "terminé": "termine",
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


def medecin_has_confirmed_slot(medecin, date, heure, exclude_id=None):
    conflicts = RendezVous.objects.filter(
        medecin=medecin,
        date=date,
        heure=heure,
        statut="confirme",
    )
    if exclude_id:
        conflicts = conflicts.exclude(id=exclude_id)
    return conflicts.exists()


@csrf_exempt
def rendezvous_list(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return create_public_rdv(request)
        return create_rdv(request)

    if not request.user.is_authenticated:
        return json_error("Unauthorized", 401)

    if request.method != "GET":
        return json_error("Method not allowed", 405)

    role = request.user.role
    rdvs = RendezVous.objects.select_related("patient__user", "medecin__user")

    if role in ["admin", "secretaire"]:
        pass
    elif role == "medecin":
        rdvs = rdvs.filter(medecin__user=request.user, statut="confirme")
    elif role == "patient":
        rdvs = rdvs.filter(patient__user=request.user)
    else:
        log_security_event(request.user, "forbidden_access", f"forbidden access to {request.path} with role {role}", request)
        return json_error("Forbidden", 403)

    log_action(request.user, "sensitive_access", "rendezvous.RendezVous", "", "rendezvous list access", request)
    return JsonResponse([serialize_rdv(r) for r in rdvs], safe=False)


@csrf_exempt
@method_required("POST")
def create_public_rdv(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["nom", "email", "telephone", "date", "heure"])
    if not data.get("medecin_id") and not data.get("specialite"):
        missing.append("medecin_id or specialite")
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        nom = require_string(data, "nom", 150)
        email = require_string(data, "email", 150).lower()
        telephone = require_string(data, "telephone", 20)
        date = require_string(data, "date", 20)
        heure = require_string(data, "heure", 20)
        medecin_id = None
        if data.get("medecin_id"):
            medecin_id = require_int(data, "medecin_id")
        specialite = optional_string(data, "specialite", 100)
        validate_email(email)
    except (SuspiciousOperation, ValidationError):
        return json_error("Invalid input", 400)

    parsed_date = parse_date(date)
    parsed_heure = parse_time(heure)
    if parsed_date is None or parsed_heure is None:
        return json_error("Invalid date or time", 400)

    try:
        if medecin_id:
            medecin = Medecin.objects.get(id=medecin_id, disponible=True)
        else:
            medecin = Medecin.objects.filter(
                specialite__iexact=specialite,
                disponible=True,
            ).select_related("user").first()
            if not medecin:
                medecin = Medecin.objects.filter(disponible=True).select_related("user").first()
    except Medecin.DoesNotExist:
        return json_error("Medecin not found", 404)

    if not medecin:
        return json_error("No available medecin", 404)

    temporary_password = None
    account_created = False

    with transaction.atomic():
        user = User.objects.filter(username=email).first()
        if user:
            if user.role != "patient":
                return json_error("Email already used by another account", 400)
            patient, _ = Patient.objects.get_or_create(user=user, defaults={"telephone": telephone})
            if not patient.telephone:
                patient.telephone = telephone
                patient.save(update_fields=["telephone"])
        else:
            temporary_password = get_random_string(14)
            user = User.objects.create_user(
                username=email,
                email=email,
                password=temporary_password,
                role="patient",
                first_name=nom,
            )
            patient = Patient.objects.create(user=user, telephone=telephone)
            account_created = True

        rdv = RendezVous.objects.create(
            patient=patient,
            medecin=medecin,
            date=parsed_date,
            heure=parsed_heure,
        )

    log_action(user, "create", "rendezvous.RendezVous", rdv.id, "public appointment", request)

    response = {
        "message": "Rendez-vous cree. Un compte patient a ete cree pour vous." if account_created else "Rendez-vous cree avec votre compte patient existant.",
        "appointment": serialize_rdv(rdv),
        "username": user.username,
        "account_created": account_created,
    }
    if temporary_password:
        response["password"] = temporary_password
        response["password_temporaire"] = temporary_password

    return JsonResponse(response, status=201)


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

    if medecin_has_confirmed_slot(medecin, date, heure):
        return json_error("This appointment slot is already confirmed for this doctor", 400)

    rdv = RendezVous.objects.create(
        patient=patient,
        medecin=medecin,
        date=date,
        heure=heure,
    )
    log_action(request.user, "create", "rendezvous.RendezVous", rdv.id, request=request)
    return JsonResponse(serialize_rdv(rdv), status=201)


@csrf_exempt
@method_required("POST", "PUT")
@require_roles("secretaire")
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
        rdv = RendezVous.objects.get(id=id)
    except RendezVous.DoesNotExist:
        return json_error("Rendez-vous not found", 404)

    if statut == "confirme" and medecin_has_confirmed_slot(rdv.medecin, rdv.date, rdv.heure, exclude_id=rdv.id):
        return json_error("This appointment slot is already confirmed for this doctor", 400)

    rdv.statut = statut
    rdv.save(update_fields=["statut"])
    log_action(request.user, "update", "rendezvous.RendezVous", rdv.id, request=request)
    return JsonResponse(serialize_rdv(rdv))
