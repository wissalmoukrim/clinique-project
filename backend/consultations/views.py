from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Consultation, Ordonnance, Medicament
from rendezvous.models import RendezVous
from medecins.models import Medecin
import json


# ================= LIST CONSULTATIONS =================
@csrf_exempt
def consultation_list(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    role = request.user.role
    username = request.user.username

    if role == "admin":
        consultations = Consultation.objects.all()

    elif role == "medecin":
        consultations = Consultation.objects.filter(medecin__user__username=username)

    elif role == "patient":
        consultations = Consultation.objects.filter(patient__user__username=username)

    else:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    data = []

    for c in consultations:
        ordonnance = getattr(c, "ordonnance", None)

        medicaments = []
        if ordonnance:
            medicaments = [
                {
                    "nom": m.nom,
                    "dosage": m.dosage,
                    "frequence": m.frequence,
                    "duree": m.duree
                }
                for m in ordonnance.medicaments.all()
            ]

        data.append({
            "id": c.id,
            "patient": c.patient.user.username,
            "medecin": c.medecin.user.username,
            "date": str(c.date),
            "diagnostic": c.diagnostic,
            "traitement": c.traitement,
            "medicaments": medicaments
        })

    return JsonResponse(data, safe=False)


# ================= CREATE CONSULTATION =================
@csrf_exempt
def create_consultation(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role != "medecin":
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            rdv = RendezVous.objects.get(id=data.get("rdv_id"))
            medecin = Medecin.objects.get(user=request.user)

            consultation = Consultation.objects.create(
                patient=rdv.patient,
                medecin=medecin,
                rendezvous=rdv,
                diagnostic=data.get("diagnostic"),
                traitement=data.get("traitement", "")
            )

            # 🔥 création ordonnance
            ordonnance = Ordonnance.objects.create(
                consultation=consultation
            )

            # 🔥 ajout médicaments
            meds = data.get("medicaments", [])

            for m in meds:
                Medicament.objects.create(
                    ordonnance=ordonnance,
                    nom=m.get("nom"),
                    dosage=m.get("dosage"),
                    frequence=m.get("frequence"),
                    duree=m.get("duree")
                )

            return JsonResponse({"message": "Consultation + ordonnance créée ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)