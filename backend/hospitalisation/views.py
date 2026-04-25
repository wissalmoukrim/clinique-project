from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Hospitalisation, Chambre
from consultations.models import Consultation
import json


# ================= LIST =================
@csrf_exempt
def hospitalisation_list(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    role = request.user.role
    username = request.user.username

    if role in ["admin", "secretaire"]:
        hosp = Hospitalisation.objects.all()

    elif role == "medecin":
        hosp = Hospitalisation.objects.filter(
            consultation__medecin__user__username=username
        )

    elif role == "patient":
        hosp = Hospitalisation.objects.filter(
            patient__user__username=username
        )

    else:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    data = [
        {
            "id": h.id,
            "patient": h.patient.user.username,
            "chambre": h.chambre.numero if h.chambre else None,
            "date_entree": str(h.date_entree),
            "date_sortie": str(h.date_sortie) if h.date_sortie else None,
            "statut": h.statut,
            "motif": h.motif
        }
        for h in hosp
    ]

    return JsonResponse(data, safe=False)


# ================= CREATE =================
@csrf_exempt
def create_hospitalisation(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role not in ["admin", "medecin"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            consultation = Consultation.objects.get(id=data.get("consultation_id"))
            chambre = Chambre.objects.get(id=data.get("chambre_id"))

            hosp = Hospitalisation.objects.create(
                patient=consultation.patient,
                consultation=consultation,
                chambre=chambre,
                date_entree=data.get("date_entree"),
                motif=data.get("motif")
            )

            # 🔥 rendre chambre indisponible
            chambre.disponible = False
            chambre.save()

            return JsonResponse({"message": "Hospitalisation créée ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# ================= SORTIE =================
@csrf_exempt
def sortie_patient(request, id):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role not in ["admin", "medecin"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            hosp = Hospitalisation.objects.get(id=id)

            hosp.date_sortie = data.get("date_sortie")
            hosp.statut = "sorti"
            hosp.save()

            # 🔥 libérer chambre
            if hosp.chambre:
                hosp.chambre.disponible = True
                hosp.chambre.save()

            return JsonResponse({"message": "Patient sorti ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)