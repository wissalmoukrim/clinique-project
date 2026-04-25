from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Ambulance, MissionAmbulance
from personnel.models import Personnel
import json


# ================= LIST =================
@csrf_exempt
def ambulance_list(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    # admin voit tout
    if request.user.role != "admin":
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    ambulances = Ambulance.objects.all()

    data = [
        {
            "id": a.id,
            "matricule": a.matricule,
            "type": a.type,
            "disponible": a.disponible,
            "chauffeur": a.chauffeur.user.username if a.chauffeur else None
        }
        for a in ambulances
    ]

    return JsonResponse(data, safe=False)


# ================= CREATE MISSION =================
@csrf_exempt
def create_mission(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    # admin ou chauffeur
    if request.user.role not in ["admin", "chauffeur"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            ambulance = Ambulance.objects.get(id=data.get("ambulance_id"))
            chauffeur = Personnel.objects.get(user=request.user)

            if not ambulance.disponible:
                return JsonResponse({"error": "Ambulance non disponible"}, status=400)

            mission = MissionAmbulance.objects.create(
                ambulance=ambulance,
                chauffeur=chauffeur,
                patient_nom=data.get("patient_nom"),
                lieu_depart=data.get("lieu_depart"),
                lieu_arrivee=data.get("lieu_arrivee")
            )

            # 🔥 rendre ambulance occupée
            ambulance.disponible = False
            ambulance.save()

            return JsonResponse({"message": "Mission créée ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# ================= TERMINER MISSION =================
@csrf_exempt
def terminer_mission(request, id):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role not in ["admin", "chauffeur"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            mission = MissionAmbulance.objects.get(id=id)

            mission.statut = "terminée"
            mission.save()

            # 🔥 libérer ambulance
            mission.ambulance.disponible = True
            mission.ambulance.save()

            return JsonResponse({"message": "Mission terminée ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)