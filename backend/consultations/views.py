from django.http import JsonResponse
from django.core.exceptions import SuspiciousOperation
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt

from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, log_security_event, optional_string, parse_json_body, require_fields, require_int, require_string
from facturation.models import Facture
from medecins.models import Medecin
from rendezvous.models import RendezVous
from .models import Consultation, Medicament, Ordonnance

DEFAULT_CONSULTATION_AMOUNT = "300.00"


def serialize_consultation(consultation):
    ordonnance = getattr(consultation, "ordonnance", None)
    medicaments = []
    if ordonnance:
        medicaments = [
            {
                "nom": m.nom,
                "dosage": m.dosage,
                "frequence": m.frequence,
                "duree": m.duree,
            }
            for m in ordonnance.medicaments.all()
        ]

    return {
        "id": consultation.id,
        "rendezvous_id": consultation.rendezvous_id,
        "patient": consultation.patient.user.username,
        "medecin": consultation.medecin.user.username,
        "date": str(consultation.date),
        "diagnostic": consultation.diagnostic,
        "notes": consultation.notes,
        "traitement": consultation.traitement,
        "medicaments": medicaments,
    }


@csrf_exempt
def consultation_list(request):
    if not request.user.is_authenticated:
        return json_error("Unauthorized", 401)
    if request.method == "POST":
        return create_consultation(request)
    if request.method != "GET":
        return json_error("Method not allowed", 405)

    role = request.user.role
    consultations = Consultation.objects.select_related("patient__user", "medecin__user").prefetch_related("ordonnance__medicaments")

    if role == "admin":
        pass
    elif role == "medecin":
        consultations = consultations.filter(medecin__user=request.user)
    elif role == "patient":
        consultations = consultations.filter(patient__user=request.user)
    else:
        log_security_event(request.user, "forbidden_access", f"forbidden access to {request.path} with role {role}", request)
        return json_error("Forbidden", 403)

    log_action(request.user, "sensitive_access", "consultations.Consultation", "", "sensitive consultation access", request)
    return JsonResponse([serialize_consultation(c) for c in consultations], safe=False)


@csrf_exempt
@method_required("POST")
@require_roles("medecin")
def create_consultation(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["rdv_id", "diagnostic"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        rdv_id = require_int(data, "rdv_id")
        diagnostic = require_string(data, "diagnostic", 4000)
        traitement = optional_string(data, "traitement", 4000)
        notes = optional_string(data, "notes", 4000)
        medicaments = data.get("medicaments", [])
        if not isinstance(medicaments, list):
            raise SuspiciousOperation("Invalid input")
        validated_medicaments = []
        for item in medicaments:
            if not isinstance(item, dict):
                raise SuspiciousOperation("Invalid input")
            missing_med = require_fields(item, ["nom", "dosage", "frequence", "duree"])
            if missing_med:
                continue
            validated_medicaments.append({
                "nom": require_string(item, "nom", 100),
                "dosage": require_string(item, "dosage", 100),
                "frequence": require_string(item, "frequence", 100),
                "duree": require_string(item, "duree", 100),
            })
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    try:
        medecin = Medecin.objects.get(user=request.user)
    except Medecin.DoesNotExist:
        return json_error("Medecin not found", 404)

    with transaction.atomic():
        try:
            rdv = RendezVous.objects.select_for_update().select_related("patient", "medecin__user").get(id=rdv_id)
        except RendezVous.DoesNotExist:
            return json_error("Rendez-vous not found", 404)

        if rdv.medecin.user_id != request.user.id or rdv.medecin_id != medecin.id:
            log_security_event(request.user, "forbidden_access", f"forbidden consultation create for rdv {rdv.id}", request)
            return json_error("Forbidden", 403)

        if Consultation.objects.filter(rendezvous=rdv).exists():
            return JsonResponse({"error": "Consultation already exists for this appointment"}, status=400)

        if rdv.statut != "confirme":
            return json_error("Rendez-vous must be confirmed before creating a consultation", 400)

        consultation = Consultation.objects.create(
            patient=rdv.patient,
            medecin=medecin,
            rendezvous=rdv,
            diagnostic=diagnostic,
            notes=notes,
            traitement=traitement,
        )
        ordonnance = Ordonnance.objects.create(consultation=consultation, notes=notes)

        for item in validated_medicaments:
            Medicament.objects.create(
                ordonnance=ordonnance,
                nom=item["nom"],
                dosage=item["dosage"],
                frequence=item["frequence"],
                duree=item["duree"],
            )

        rdv.statut = "termine"
        rdv.save(update_fields=["statut"])

        facture = Facture.objects.create(
            patient=consultation.patient,
            consultation=consultation,
            montant=DEFAULT_CONSULTATION_AMOUNT,
        )

    log_action(request.user, "create", "consultations.Consultation", consultation.id, request=request)
    log_action(request.user, "create", "facturation.Facture", facture.id, "auto consultation invoice", request)
    return JsonResponse(serialize_consultation(consultation), status=201)
