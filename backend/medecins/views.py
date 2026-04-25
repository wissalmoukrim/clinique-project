from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Medecin
from accounts.models import User
import json


# ================= LIST =================
@csrf_exempt
def medecin_list(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    # 🔒 accessible à tous les rôles internes
    if request.user.role not in [
        "admin", "secretaire", "infirmier", "medecin"
    ]:
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    medecins = Medecin.objects.all()

    data = [
        {
            "id": m.id,
            "username": m.user.username,
            "specialite": m.specialite,
            "disponible": m.disponible
        }
        for m in medecins
    ]

    return JsonResponse(data, safe=False)


# ================= CREATE =================
@csrf_exempt
def create_medecin(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    # 🔒 admin uniquement
    if request.user.role != "admin":
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            user = User.objects.get(id=data.get("user_id"))

            if user.role != "medecin":
                return JsonResponse({"error": "User must be medecin"}, status=400)

            medecin = Medecin.objects.create(
                user=user,
                specialite=data.get("specialite"),
                telephone=data.get("telephone", ""),
                numero_ordre=data.get("numero_ordre"),
                disponible=True
            )

            return JsonResponse({"message": "Médecin créé ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


# ================= MY PROFILE =================
@csrf_exempt
def my_medecin_profile(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role != "medecin":
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    try:
        medecin = Medecin.objects.get(user=request.user)

        data = {
            "username": medecin.user.username,
            "specialite": medecin.specialite,
            "telephone": medecin.telephone,
            "disponible": medecin.disponible
        }

        return JsonResponse(data)

    except Medecin.DoesNotExist:
        return JsonResponse({"error": "Profil introuvable"}, status=404)