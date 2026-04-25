from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Personnel
from accounts.models import User
import json


# ================= LIST PERSONNEL =================
@csrf_exempt
def personnel_list(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    # 🔒 admin seulement
    if request.user.role != "admin":
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    personnels = Personnel.objects.all()

    data = [
        {
            "id": p.id,
            "username": p.user.username,
            "role": p.user.role,
            "fonction": p.fonction,
            "actif": p.actif
        }
        for p in personnels
    ]

    return JsonResponse(data, safe=False)


# ================= CREATE PERSONNEL =================
@csrf_exempt
def create_personnel(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized ❌"}, status=401)

    if request.user.role != "admin":
        return JsonResponse({"error": "Forbidden ❌"}, status=403)

    if request.method == "POST":
        try:
            data = json.loads(request.body)

            user = User.objects.get(id=data.get("user_id"))

            personnel = Personnel.objects.create(
                user=user,
                fonction=user.role,  # 🔥 aligné automatiquement
                telephone=data.get("telephone", ""),
                adresse=data.get("adresse", "")
            )

            return JsonResponse({"message": "Personnel créé ✅"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)