from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, parse_json_body, require_fields
from medecins.models import Medecin
from rendezvous.models import RendezVous
from .models import Consultation, Medicament, Ordonnance


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
        "patient": consultation.patient.user.username,
        "medecin": consultation.medecin.user.username,
        "date": str(consultation.date),
        "diagnostic": consultation.diagnostic,
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
        return json_error("Forbidden", 403)

    log_action(request.user, "update", "consultations.Consultation", "", "sensitive consultation access", request)
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
        rdv = RendezVous.objects.select_related("patient", "medecin__user").get(id=data["rdv_id"])
    except RendezVous.DoesNotExist:
        return json_error("Rendez-vous not found", 404)

    try:
        medecin = Medecin.objects.get(user=request.user)
    except Medecin.DoesNotExist:
        return json_error("Medecin not found", 404)

    if rdv.medecin_id != medecin.id:
        return json_error("Forbidden", 403)

    if Consultation.objects.filter(rendezvous=rdv).exists():
        return json_error("Consultation already exists for this rendez-vous", 400)

    consultation = Consultation.objects.create(
        patient=rdv.patient,
        medecin=medecin,
        rendezvous=rdv,
        diagnostic=data["diagnostic"],
        traitement=data.get("traitement", ""),
    )
    ordonnance = Ordonnance.objects.create(consultation=consultation, notes=data.get("notes", ""))

    for item in data.get("medicaments", []):
        missing_med = require_fields(item, ["nom", "dosage", "frequence", "duree"])
        if missing_med:
            continue
        Medicament.objects.create(
            ordonnance=ordonnance,
            nom=item["nom"],
            dosage=item["dosage"],
            frequence=item["frequence"],
            duree=item["duree"],
        )

    log_action(request.user, "create", "consultations.Consultation", consultation.id, request=request)
    return JsonResponse(serialize_consultation(consultation), status=201)
