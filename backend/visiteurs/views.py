from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Visiteur, JournalVisite
from personnel.models import Personnel
import json
from django.utils import timezone


# ================= LIST VISITEURS =================
@csrf_exempt
def visiteur_list(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role not in ["admin", "securite", "secretaire"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    visiteurs = Visiteur.objects.all()

    data = [
        {
            "id": v.id,
            "nom": v.nom,
            "prenom": v.prenom,
            "cin": v.cin,
            "telephone": v.telephone
        }
        for v in visiteurs
    ]

    return JsonResponse(data, safe=False)


# ================= CREATE VISITEUR =================
@csrf_exempt
def create_visiteur(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role not in ["admin", "securite", "secretaire"]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            visiteur = Visiteur.objects.create(
                nom=data.get("nom"),
                prenom=data.get("prenom"),
                cin=data.get("cin"),
                telephone=data.get("telephone", "")
            )

            return JsonResponse({"message": "Visiteur créé ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# ================= ENTRÉE VISITEUR =================
@csrf_exempt
def entree_visiteur(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role != "securite":
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            visiteur = Visiteur.objects.get(id=data.get("visiteur_id"))
            agent = Personnel.objects.get(user=request.user)

            JournalVisite.objects.create(
                visiteur=visiteur,
                agent_securite=agent,
                motif=data.get("motif", "visite")
            )

            return JsonResponse({"message": "Entrée enregistrée ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# ================= SORTIE VISITEUR =================
@csrf_exempt
def sortie_visiteur(request, id):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role != "securite":
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)  # ✅ CORRECTION ICI

            visite = JournalVisite.objects.get(id=id)

            # si date non envoyée → maintenant
            date_sortie = data.get("date_sortie")
            if date_sortie:
                visite.date_sortie = date_sortie
            else:
                visite.date_sortie = timezone.now()

            visite.statut = "terminé"
            visite.save()

            return JsonResponse({"message": "Sortie enregistrée ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)