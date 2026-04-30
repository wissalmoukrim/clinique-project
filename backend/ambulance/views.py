from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, parse_json_body, require_fields
from personnel.models import Personnel
from .models import Ambulance, MissionAmbulance


def serialize_ambulance(ambulance):
    return {
        "id": ambulance.id,
        "matricule": ambulance.matricule,
        "type": ambulance.type,
        "disponible": ambulance.disponible,
        "chauffeur": ambulance.chauffeur.user.username if ambulance.chauffeur else None,
    }


def serialize_mission(mission):
    return {
        "id": mission.id,
        "ambulance": mission.ambulance.matricule,
        "chauffeur": mission.chauffeur.user.username if mission.chauffeur else None,
        "patient_nom": mission.patient_nom,
        "lieu_depart": mission.lieu_depart,
        "lieu_arrivee": mission.lieu_arrivee,
        "date": str(mission.date),
        "statut": mission.statut,
    }


@csrf_exempt
@require_roles("admin", "chauffeur")
def ambulance_list(request):
    if request.method == "GET":
        ambulances = Ambulance.objects.select_related("chauffeur__user").all()
        if request.user.role == "chauffeur":
            ambulances = ambulances.filter(chauffeur__user=request.user)
        return JsonResponse([serialize_ambulance(a) for a in ambulances], safe=False)

    if request.method == "POST":
        return create_ambulance(request)

    return json_error("Method not allowed", 405)


@csrf_exempt
@method_required("POST")
@require_roles("admin")
def create_ambulance(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["matricule", "type"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    chauffeur = None
    if data.get("chauffeur_id"):
        try:
            chauffeur = Personnel.objects.get(id=data["chauffeur_id"], fonction="chauffeur")
        except Personnel.DoesNotExist:
            return json_error("Chauffeur not found", 404)

    if Ambulance.objects.filter(matricule=data["matricule"]).exists():
        return json_error("Ambulance already exists", 400)

    ambulance = Ambulance.objects.create(
        matricule=data["matricule"],
        type=data["type"],
        chauffeur=chauffeur,
        disponible=bool(data.get("disponible", True)),
    )
    log_action(request.user, "create", "ambulance.Ambulance", ambulance.id, request=request)
    return JsonResponse(serialize_ambulance(ambulance), status=201)


@csrf_exempt
@method_required("GET")
@require_roles("admin", "chauffeur")
def mission_list(request):
    missions = MissionAmbulance.objects.select_related("ambulance", "chauffeur__user").all()
    if request.user.role == "chauffeur":
        missions = missions.filter(chauffeur__user=request.user)
    return JsonResponse([serialize_mission(m) for m in missions], safe=False)


@csrf_exempt
@method_required("POST")
@require_roles("admin", "chauffeur")
def create_mission(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["ambulance_id", "patient_nom", "lieu_depart", "lieu_arrivee"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        ambulance = Ambulance.objects.get(id=data["ambulance_id"])
    except Ambulance.DoesNotExist:
        return json_error("Ambulance not found", 404)

    try:
        if request.user.role == "chauffeur":
            chauffeur = Personnel.objects.get(user=request.user, fonction="chauffeur")
        else:
            chauffeur_id = data.get("chauffeur_id")
            chauffeur = Personnel.objects.get(id=chauffeur_id, fonction="chauffeur") if chauffeur_id else ambulance.chauffeur
    except Personnel.DoesNotExist:
        return json_error("Chauffeur not found", 404)

    if not chauffeur:
        return json_error("Missing fields: chauffeur_id", 400)
    if not ambulance.disponible:
        return json_error("Ambulance not available", 400)
    if request.user.role == "chauffeur" and ambulance.chauffeur_id and ambulance.chauffeur_id != chauffeur.id:
        return json_error("Forbidden", 403)

    mission = MissionAmbulance.objects.create(
        ambulance=ambulance,
        chauffeur=chauffeur,
        patient_nom=data["patient_nom"],
        lieu_depart=data["lieu_depart"],
        lieu_arrivee=data["lieu_arrivee"],
    )
    ambulance.disponible = False
    ambulance.save(update_fields=["disponible"])
    log_action(request.user, "create", "ambulance.MissionAmbulance", mission.id, request=request)
    return JsonResponse({"id": mission.id, "message": "Mission created"}, status=201)


@csrf_exempt
@method_required("POST")
@require_roles("admin", "chauffeur")
def terminer_mission(request, id):
    try:
        mission = MissionAmbulance.objects.select_related("ambulance", "chauffeur__user").get(id=id)
    except MissionAmbulance.DoesNotExist:
        return json_error("Mission not found", 404)

    if request.user.role == "chauffeur" and mission.chauffeur.user_id != request.user.id:
        return json_error("Forbidden", 403)

    mission.statut = MissionAmbulance.STATUT_CHOICES[1][0]
    mission.save(update_fields=["statut"])
    mission.ambulance.disponible = True
    mission.ambulance.save(update_fields=["disponible"])
    log_action(request.user, "update", "ambulance.MissionAmbulance", mission.id, "terminated", request)
    return JsonResponse({"message": "Mission terminated"})
