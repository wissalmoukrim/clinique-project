from django.http import JsonResponse
from django.core.exceptions import SuspiciousOperation
from django.core.validators import validate_email
from django.db import transaction
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt

from accounts.models import User
from consultations.models import Consultation
from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, optional_string, parse_json_body, require_fields, require_int, require_string
from rendezvous.models import RendezVous
from .models import Patient
from .serializers import PatientSerializer


def serialize_patient(patient):
    return PatientSerializer(patient).data


@csrf_exempt
@require_roles("admin", "secretaire", "infirmier", "medecin", "comptable")
def patient_list(request):
    if request.method == "GET":
        patients = Patient.objects.select_related("user").all()
        if request.user.role == "medecin":
            consultation_patient_ids = Consultation.objects.filter(
                medecin__user=request.user,
            ).values_list("patient_id", flat=True)
            rendezvous_patient_ids = RendezVous.objects.filter(
                medecin__user=request.user,
            ).values_list("patient_id", flat=True)
            patients = patients.filter(
                id__in=list(consultation_patient_ids) + list(rendezvous_patient_ids),
            ).distinct()
        log_action(request.user, "sensitive_access", "patients.Patient", "", "sensitive patient list access", request)
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
        user_id = require_int(data, "user_id")
        telephone = optional_string(data, "telephone", 20)
        adresse = optional_string(data, "adresse", 255)
        date_naissance = optional_string(data, "date_naissance", 20) or None
        sexe = optional_string(data, "sexe", 10)
        groupe_sanguin = optional_string(data, "groupe_sanguin", 5)
        allergies = optional_string(data, "allergies", 2000)
        antecedents = optional_string(data, "antecedents", 2000)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return json_error("User not found", 404)

    if user.role != "patient":
        return json_error("User must have patient role", 400)

    if Patient.objects.filter(user=user).exists():
        return json_error("Patient profile already exists", 400)

    patient = Patient.objects.create(
        user=user,
        telephone=telephone,
        adresse=adresse,
        date_naissance=date_naissance,
        sexe=sexe,
        groupe_sanguin=groupe_sanguin,
        allergies=allergies,
        antecedents=antecedents,
    )
    log_action(request.user, "create", "patients.Patient", patient.id, request=request)
    return JsonResponse(serialize_patient(patient), status=201)


@csrf_exempt
@method_required("POST")
@require_roles("admin", "secretaire")
def create_patient_account(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["full_name", "email"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        full_name = require_string(data, "full_name", 150)
        email = require_string(data, "email", 150).lower()
        telephone = optional_string(data, "telephone", 20)
        adresse = optional_string(data, "adresse", 255)
        validate_email(email)
    except Exception:
        return json_error("Invalid input", 400)

    if User.objects.filter(username=email).exists() or User.objects.filter(email=email).exists():
        return json_error("User already exists", 400)

    temporary_password = get_random_string(14) + "aA1!"
    name_parts = full_name.split(" ", 1)

    with transaction.atomic():
        user = User.objects.create_user(
            username=email,
            email=email,
            password=temporary_password,
            role="patient",
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else "",
        )
        patient = Patient.objects.create(
            user=user,
            telephone=telephone,
            adresse=adresse,
        )

    log_action(request.user, "register", "accounts.User", user.id, "secretary patient account", request)
    log_action(request.user, "create", "patients.Patient", patient.id, request=request)
    response = serialize_patient(patient)
    response["temporary_password"] = temporary_password
    return JsonResponse(response, status=201)


@csrf_exempt
@method_required("GET")
@require_roles("patient")
def my_profile(request):
    try:
        patient = Patient.objects.select_related("user").get(user=request.user)
    except Patient.DoesNotExist:
        return json_error("Patient not found", 404)
    log_action(request.user, "sensitive_access", "patients.Patient", patient.id, "patient profile access", request)
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


@csrf_exempt
@method_required("PUT", "PATCH")
@require_roles("admin", "secretaire")
def update_patient(request, patient_id):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return json_error("Patient not found", 404)

    try:
        if "telephone" in data:
            patient.telephone = optional_string(data, "telephone", 20)
        if "adresse" in data:
            patient.adresse = optional_string(data, "adresse", 255)
        if "date_naissance" in data:
            patient.date_naissance = optional_string(data, "date_naissance", 20) or None
        if "sexe" in data:
            patient.sexe = optional_string(data, "sexe", 10)
        if "groupe_sanguin" in data:
            patient.groupe_sanguin = optional_string(data, "groupe_sanguin", 5)
        if "allergies" in data:
            patient.allergies = optional_string(data, "allergies", 2000)
        if "antecedents" in data:
            patient.antecedents = optional_string(data, "antecedents", 2000)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    patient.save()
    log_action(request.user, "update", "patients.Patient", patient.id, request=request)
    return JsonResponse(serialize_patient(patient))
