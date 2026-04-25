from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import RendezVous
from patients.models import Patient
from medecins.models import Medecin
import json


# ================= LIST RDV =================
@csrf_exempt
def rendezvous_list(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    role = request.user.role
    username = request.user.username

    # 🔥 ADMIN / SECRETAIRE → tout
    if role in ["admin", "secretaire"]:
        rdvs = RendezVous.objects.all()

    # 🔥 MEDECIN → ses RDV
    elif role == "medecin":
        rdvs = RendezVous.objects.filter(medecin__user__username=username)

    # 🔥 PATIENT → ses RDV
    elif role == "patient":
        rdvs = RendezVous.objects.filter(patient__user__username=username)

    else:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    data = [
        {
            "id": r.id,
            "patient": r.patient.user.username,
            "medecin": r.medecin.user.username,
            "date": r.date,
            "heure": r.heure,
            "statut": r.statut
        }
        for r in rdvs
    ]

    return JsonResponse(data, safe=False)


# ================= CREATE RDV =================
@csrf_exempt
def create_rdv(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role not in ["admin", "secretaire"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            patient = Patient.objects.get(id=data.get("patient_id"))
            medecin = Medecin.objects.get(id=data.get("medecin_id"))

            rdv = RendezVous.objects.create(
                patient=patient,
                medecin=medecin,
                date=data.get("date"),
                heure=data.get("heure"),
                statut="en attente"
            )

            return JsonResponse({"message": "RDV créé ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# ================= UPDATE STATUT =================
@csrf_exempt
def update_rdv_status(request, id):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role not in ["admin", "secretaire"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            rdv = RendezVous.objects.get(id=id)
            rdv.statut = data.get("statut")
            rdv.save()

            return JsonResponse({"message": "Statut mis à jour ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)