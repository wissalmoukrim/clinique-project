from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from consultations.models import Consultation
from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, parse_json_body, require_fields
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
        return json_error("Forbidden", 403)

    log_action(request.user, "update", "facturation.Facture", "", "sensitive billing access", request)
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
        patient = Patient.objects.get(id=data["patient_id"])
    except Patient.DoesNotExist:
        return json_error("Patient not found", 404)

    consultation = None
    hospitalisation = None
    if data.get("consultation_id"):
        try:
            consultation = Consultation.objects.get(id=data["consultation_id"])
        except Consultation.DoesNotExist:
            return json_error("Consultation not found", 404)
    if data.get("hospitalisation_id"):
        try:
            hospitalisation = Hospitalisation.objects.get(id=data["hospitalisation_id"])
        except Hospitalisation.DoesNotExist:
            return json_error("Hospitalisation not found", 404)

    facture = Facture.objects.create(
        patient=patient,
        consultation=consultation,
        hospitalisation=hospitalisation,
        montant=data["montant"],
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
        facture = Facture.objects.get(id=id)
    except Facture.DoesNotExist:
        return json_error("Facture not found", 404)

    if Paiement.objects.filter(facture=facture).exists():
        return json_error("Facture already paid", 400)

    Paiement.objects.create(facture=facture, montant=facture.montant, mode=data["mode"])
    facture.statut = Facture.STATUT_CHOICES[1][0]
    facture.save(update_fields=["statut"])
    log_action(request.user, "update", "facturation.Facture", facture.id, "payment", request)
    return JsonResponse(serialize_facture(facture))
