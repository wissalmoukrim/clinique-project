from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, parse_json_body, require_fields
from .models import Patient


def serialize_patient(patient):
    return {
        "id": patient.id,
        "user_id": patient.user_id,
        "username": patient.user.username,
        "telephone": patient.telephone,
        "adresse": patient.adresse,
        "date_naissance": str(patient.date_naissance) if patient.date_naissance else None,
        "sexe": patient.sexe,
        "groupe_sanguin": patient.groupe_sanguin,
        "allergies": patient.allergies,
        "antecedents": patient.antecedents,
    }


@csrf_exempt
@require_roles("admin", "secretaire", "infirmier", "medecin")
def patient_list(request):
    if request.method == "GET":
        patients = Patient.objects.select_related("user").all()
        log_action(request.user, "update", "patients.Patient", "", "sensitive patient list access", request)
        return JsonResponse([serialize_patient(p) for p in patients], safe=False)
    if request.method == "POST":
        return create_patient(request)
    return json_error("Method not allowed", 405)


@csrf_exempt
@method_required("POST")
@require_roles("admin", "secretaire")
def create_patient(request):
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

    if user.role != "patient":
        return json_error("User must have patient role", 400)

    if Patient.objects.filter(user=user).exists():
        return json_error("Patient profile already exists", 400)

    patient = Patient.objects.create(
        user=user,
        telephone=data.get("telephone", ""),
        adresse=data.get("adresse", ""),
        date_naissance=data.get("date_naissance") or None,
        sexe=data.get("sexe", ""),
        groupe_sanguin=data.get("groupe_sanguin", ""),
        allergies=data.get("allergies", ""),
        antecedents=data.get("antecedents", ""),
    )
    log_action(request.user, "create", "patients.Patient", patient.id, request=request)
    return JsonResponse(serialize_patient(patient), status=201)


@csrf_exempt
@method_required("GET")
@require_roles("patient")
def my_profile(request):
    try:
        patient = Patient.objects.select_related("user").get(user=request.user)
    except Patient.DoesNotExist:
        return json_error("Patient not found", 404)
    log_action(request.user, "update", "patients.Patient", patient.id, "patient profile access", request)
    return JsonResponse(serialize_patient(patient))


@csrf_exempt
@method_required("DELETE")
@require_roles("admin")
def delete_patient(request, patient_id):
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return json_error("Patient not found", 404)

    patient.delete()
    log_action(request.user, "delete", "patients.Patient", patient_id, request=request)
    return JsonResponse({"message": "Patient deleted"})
