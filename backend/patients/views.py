from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Patient
from accounts.models import User
import json


# ================= LIST PATIENTS =================
@csrf_exempt
def patient_list(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    role = request.user.role

    # 🔒 admin / secretaire / infirmier
    if role not in ["admin", "secretaire", "infirmier"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    patients = Patient.objects.all()

    data = [
        {
            "id": p.id,
            "username": p.user.username,
            "telephone": p.telephone,
            "groupe_sanguin": p.groupe_sanguin
        }
        for p in patients
    ]

    return JsonResponse(data, safe=False)


# ================= GET MY PROFILE =================
@csrf_exempt
def my_profile(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role != "patient":
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    try:
        patient = Patient.objects.get(user=request.user)

        data = {
            "username": patient.user.username,
            "telephone": patient.telephone,
            "adresse": patient.adresse,
            "groupe_sanguin": patient.groupe_sanguin,
            "allergies": patient.allergies,
            "antecedents": patient.antecedents
        }

        return JsonResponse(data)

    except Patient.DoesNotExist:
        return JsonResponse({"error": "Patient not found"}, status=404)


# ================= CREATE PATIENT =================
@csrf_exempt
def create_patient(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    # 🔒 secretaire / admin
    if request.user.role not in ["admin", "secretaire"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            user = User.objects.get(id=data.get("user_id"))

            patient = Patient.objects.create(
                user=user,
                telephone=data.get("telephone", ""),
                adresse=data.get("adresse", ""),
                groupe_sanguin=data.get("groupe_sanguin", ""),
                allergies=data.get("allergies", ""),
                antecedents=data.get("antecedents", "")
            )

            return JsonResponse({"message": "Patient créé ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)