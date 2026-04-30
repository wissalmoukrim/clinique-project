from django.core.exceptions import SuspiciousOperation
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from consultations.models import Consultation
from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, log_security_event, optional_int, parse_json_body, require_fields, require_int, require_string
from hospitalisation.models import Hospitalisation
from patients.models import Patient
from .models import Facture, Paiement


def serialize_facture(facture):
    return {
        "id": facture.id,
        "patient": facture.patient.user.username,
        "montant": float(facture.montant),
        "date": str(facture.date),
        "statut": facture.statut,
    }


@csrf_exempt
def facture_list(request):
    if not request.user.is_authenticated:
        return json_error("Unauthorized", 401)
    if request.method == "POST":
        return create_facture(request)
    if request.method != "GET":
        return json_error("Method not allowed", 405)

    role = request.user.role
    factures = Facture.objects.select_related("patient__user")

    if role in ["admin", "comptable"]:
        pass
    elif role == "patient":
        factures = factures.filter(patient__user=request.user)
    else:
        log_security_event(request.user, "forbidden_access", f"forbidden access to {request.path} with role {role}", request)
        return json_error("Forbidden", 403)

    log_action(request.user, "sensitive_access", "facturation.Facture", "", "sensitive billing access", request)
    return JsonResponse([serialize_facture(f) for f in factures], safe=False)


@csrf_exempt
@method_required("POST")
@require_roles("admin", "comptable")
def create_facture(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["patient_id", "montant"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        patient_id = require_int(data, "patient_id")
        consultation_id = optional_int(data, "consultation_id")
        hospitalisation_id = optional_int(data, "hospitalisation_id")
        montant = data.get("montant")
        if isinstance(montant, str):
            montant = require_string(data, "montant", 20)
        elif not isinstance(montant, (int, float)):
            raise SuspiciousOperation("Invalid input")
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return json_error("Patient not found", 404)

    consultation = None
    hospitalisation = None
    if consultation_id:
        try:
            consultation = Consultation.objects.get(id=consultation_id)
        except Consultation.DoesNotExist:
            return json_error("Consultation not found", 404)
    if hospitalisation_id:
        try:
            hospitalisation = Hospitalisation.objects.get(id=hospitalisation_id)
        except Hospitalisation.DoesNotExist:
            return json_error("Hospitalisation not found", 404)

    facture = Facture.objects.create(
        patient=patient,
        consultation=consultation,
        hospitalisation=hospitalisation,
        montant=montant,
    )
    log_action(request.user, "create", "facturation.Facture", facture.id, request=request)
    return JsonResponse(serialize_facture(facture), status=201)


@csrf_exempt
@method_required("POST")
@require_roles("admin", "comptable")
def payer_facture(request, id):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    if not data.get("mode"):
        return json_error("Missing fields: mode", 400)

    try:
        mode = require_string(data, "mode", 20)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    try:
        facture = Facture.objects.get(id=id)
    except Facture.DoesNotExist:
        return json_error("Facture not found", 404)

    if Paiement.objects.filter(facture=facture).exists():
        return json_error("Facture already paid", 400)

    Paiement.objects.create(facture=facture, montant=facture.montant, mode=mode)
    facture.statut = Facture.STATUT_CHOICES[1][0]
    facture.save(update_fields=["statut"])
    log_action(request.user, "update", "facturation.Facture", facture.id, "payment", request)
    return JsonResponse(serialize_facture(facture))
