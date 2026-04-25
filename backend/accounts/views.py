from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from .models import User
import json


# ================= LOGIN =================
@csrf_exempt
def login_view(request):

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)

        username = data.get("username")
        password = data.get("password")

        user = User.objects.filter(username=username).first()

        if not user:
            return JsonResponse({"error": "User not found"}, status=404)

        # 🔒 compte bloqué
        if user.is_locked:
            return JsonResponse({"error": "Account locked ❌"}, status=403)

        user_auth = authenticate(request, username=username, password=password)

        if user_auth is not None:
            login(request, user)

            # reset tentatives
            user.login_attempts = 0
            user.save()

            return JsonResponse({
                "message": "Login success",
                "username": user.username,
                "role": user.role
            })

        # ❌ mauvais mot de passe
        user.login_attempts += 1

        # 🔥 blocage après 5 essais
        if user.login_attempts >= 5:
            user.is_locked = True

        user.save()

        return JsonResponse({"error": "Invalid credentials"}, status=401)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ================= LOGOUT =================
@csrf_exempt
def logout_view(request):

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    logout(request)
    return JsonResponse({"message": "Logout success"})


# ================= REGISTER =================
@csrf_exempt
def register_view(request):

    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)

        username = data.get("username")
        password = data.get("password")
        role = data.get("role", "patient")

        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "User already exists"}, status=400)

        user = User.objects.create_user(
            username=username,
            password=password,
            role=role
        )

        return JsonResponse({
            "message": "User created",
            "username": user.username,
            "role": user.role
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)