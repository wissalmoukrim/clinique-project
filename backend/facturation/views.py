from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Facture, Paiement
from consultations.models import Consultation
from hospitalisation.models import Hospitalisation
from patients.models import Patient
import json


# ================= LIST FACTURES =================
@csrf_exempt
def facture_list(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    role = request.user.role
    username = request.user.username

    if role in ["admin", "comptable"]:
        factures = Facture.objects.all()

    elif role == "patient":
        factures = Facture.objects.filter(patient__user__username=username)

    else:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    data = [
        {
            "id": f.id,
            "patient": f.patient.user.username,
            "montant": float(f.montant),
            "date": str(f.date),
            "statut": f.statut
        }
        for f in factures
    ]

    return JsonResponse(data, safe=False)


# ================= CREATE FACTURE =================
@csrf_exempt
def create_facture(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role not in ["admin", "comptable"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            patient = Patient.objects.get(id=data.get("patient_id"))

            consultation = None
            hospitalisation = None

            if data.get("consultation_id"):
                consultation = Consultation.objects.get(id=data.get("consultation_id"))

            if data.get("hospitalisation_id"):
                hospitalisation = Hospitalisation.objects.get(id=data.get("hospitalisation_id"))

            facture = Facture.objects.create(
                patient=patient,
                consultation=consultation,
                hospitalisation=hospitalisation,
                montant=data.get("montant")
            )

            return JsonResponse({"message": "Facture créée ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# ================= PAYER FACTURE =================
@csrf_exempt
def payer_facture(request, id):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role not in ["admin", "comptable"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            facture = Facture.objects.get(id=id)

            Paiement.objects.create(
                facture=facture,
                montant=facture.montant,
                mode=data.get("mode")
            )

            facture.statut = "payé"
            facture.save()

            return JsonResponse({"message": "Paiement effectué ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)