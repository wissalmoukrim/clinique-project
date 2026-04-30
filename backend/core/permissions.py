from functools import wraps

from django.http import JsonResponse

from .utils import log_action


ROLE_ADMIN = "admin"
ROLE_MEDECIN = "medecin"
ROLE_PATIENT = "patient"
ROLE_SECRETAIRE = "secretaire"
ROLE_INFIRMIER = "infirmier"
ROLE_COMPTABLE = "comptable"
ROLE_SECURITE = "securite"
ROLE_CHAUFFEUR = "chauffeur"

ALL_ROLES = {
    ROLE_ADMIN,
    ROLE_MEDECIN,
    ROLE_PATIENT,
    ROLE_SECRETAIRE,
    ROLE_INFIRMIER,
    ROLE_COMPTABLE,
    ROLE_SECURITE,
    ROLE_CHAUFFEUR,
}


def require_roles(*roles):
    allowed_roles = set(roles)

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user = getattr(request, "user", None)
            if not user or not user.is_authenticated:
                return JsonResponse({"error": "Unauthorized"}, status=401)

            if user.role not in allowed_roles:
                log_action(
                    user,
                    "update",
                    "security",
                    "",
                    f"forbidden access to {request.path} with role {user.role}",
                    request,
                )
                return JsonResponse({"error": "Forbidden"}, status=403)

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def method_required(*methods):
    allowed_methods = {method.upper() for method in methods}

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method.upper() not in allowed_methods:
                return JsonResponse({"error": "Method not allowed"}, status=405)
            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
