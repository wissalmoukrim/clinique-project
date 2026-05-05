from django.core.exceptions import SuspiciousOperation
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, log_security_event, optional_string, parse_json_body, require_fields, require_int, require_string
from personnel.models import Personnel
from .models import JournalVisite, Visite, Visiteur


def serialize_visiteur(visiteur):
    return {
        "id": visiteur.id,
        "nom": visiteur.nom,
        "prenom": visiteur.prenom,
        "cin": visiteur.cin,
        "telephone": visiteur.telephone,
    }


def serialize_journal(journal):
    return {
        "id": journal.id,
        "visiteur_id": journal.visiteur_id,
        "visiteur": str(journal.visiteur),
        "agent_securite": journal.agent_securite.user.username if journal.agent_securite else None,
        "motif": journal.motif,
        "date_entree": str(journal.date_entree),
        "date_sortie": str(journal.date_sortie) if journal.date_sortie else None,
        "statut": journal.statut,
    }


def serialize_visite(visite):
    return {
        "id": visite.id,
        "visiteur_id": visite.visiteur_id,
        "visiteur": str(visite.visiteur),
        "motif": visite.motif,
        "date_entree": str(visite.date_entree),
        "date_sortie": str(visite.date_sortie) if visite.date_sortie else None,
        "statut": visite.statut,
    }


def normalize_journal_statut(statut):
    if statut in ["en cours", "en_cours"]:
        return "en_cours"
    if statut in ["terminé", "terminÃ©", "sorti"]:
        return "sorti"
    return statut


def get_security_personnel(user):
    personnel = Personnel.objects.filter(user=user, fonction="securite").first()
    if personnel:
        return personnel
    if user.role == "securite":
        return Personnel.objects.create(user=user, fonction="securite")
    return None


@csrf_exempt
@require_roles("admin", "securite", "secretaire")
def visiteur_list(request):
    if request.method == "GET":
        visiteurs = Visiteur.objects.all()
        return JsonResponse([serialize_visiteur(v) for v in visiteurs], safe=False)
    if request.method == "POST":
        return create_visiteur(request)
    return json_error("Method not allowed", 405)


@csrf_exempt
@method_required("POST")
@require_roles("admin", "securite", "secretaire")
def create_visiteur(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["nom", "prenom"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        nom = require_string(data, "nom", 100)
        prenom = require_string(data, "prenom", 100)
        cin = optional_string(data, "cin", 50) or None
        telephone = optional_string(data, "telephone", 20)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    visiteur = Visiteur.objects.create(
        nom=nom,
        prenom=prenom,
        cin=cin,
        telephone=telephone,
    )
    log_action(request.user, "create", "visiteurs.Visiteur", visiteur.id, request=request)
    return JsonResponse(serialize_visiteur(visiteur), status=201)


@csrf_exempt
@method_required("POST")
@require_roles("securite")
def entree_visiteur(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["visiteur_id"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        visiteur_id = require_int(data, "visiteur_id")
        motif = optional_string(data, "motif", 255) or "visite"
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    try:
        visiteur = Visiteur.objects.get(id=visiteur_id)
    except Visiteur.DoesNotExist:
        return json_error("Visiteur not found", 404)

    agent = get_security_personnel(request.user)
    if not agent:
        return json_error("Security personnel profile not found", 404)

    if Visite.objects.filter(visiteur=visiteur, statut="en_cours").exists():
        return json_error("Visitor already has an active entry", 400)

    visite = Visite.objects.create(
        visiteur=visiteur,
        motif=motif,
        date_entree=timezone.now(),
        date_sortie=None,
        statut="en_cours",
    )
    log_action(request.user, "create", "visiteurs.Visite", visite.id, f"entry by personnel {agent.id}", request)
    return JsonResponse(serialize_visite(visite), status=201)


@csrf_exempt
@method_required("POST", "PUT")
@require_roles("securite")
def sortie_visiteur(request, id):
    try:
        visite = Visite.objects.select_related("visiteur").get(id=id)
    except Visite.DoesNotExist:
        visite = None

    if visite:
        if visite.statut != "en_cours":
            return json_error("Visit already closed", 400)

        visite.date_sortie = timezone.now()
        visite.statut = "sorti"
        visite.save(update_fields=["date_sortie", "statut"])
        log_action(request.user, "update", "visiteurs.Visite", visite.id, "exit", request)
        return JsonResponse(serialize_visite(visite))

    try:
        visite = JournalVisite.objects.select_related("agent_securite__user").get(id=id)
    except JournalVisite.DoesNotExist:
        return json_error("Visit log not found", 404)

    if visite.agent_securite and visite.agent_securite.user_id != request.user.id:
        log_security_event(request.user, "forbidden_access", f"forbidden visitor exit {id}", request)
        return json_error("Forbidden", 403)

    visite.statut = normalize_journal_statut(visite.statut)
    if visite.statut != "en_cours":
        return json_error("Visit log already closed", 400)

    visite.date_sortie = timezone.now()
    visite.statut = "sorti"
    visite.save(update_fields=["date_sortie", "statut"])
    log_action(request.user, "update", "visiteurs.JournalVisite", visite.id, "exit", request)
    return JsonResponse(serialize_journal(visite))


@csrf_exempt
@method_required("GET")
@require_roles("admin", "securite", "secretaire")
def journal_visites(request):
    visites = Visite.objects.select_related("visiteur").all()
    return JsonResponse([serialize_visite(v) for v in visites], safe=False)


@csrf_exempt
@method_required("GET")
@require_roles("securite")
def visite_list(request):
    visites = Visite.objects.select_related("visiteur").all().order_by("-date_entree")
    return JsonResponse([serialize_visite(v) for v in visites], safe=False)


@csrf_exempt
@method_required("GET")
@require_roles("securite")
def visites_presentes(request):
    visites = Visite.objects.select_related("visiteur").filter(statut="en_cours").order_by("-date_entree")
    return JsonResponse([serialize_visite(v) for v in visites], safe=False)


@csrf_exempt
@method_required("POST")
@require_roles("securite")
def create_visite_entree(request):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    missing = require_fields(data, ["visiteur_id", "motif"])
    if missing:
        return json_error(f"Missing fields: {', '.join(missing)}", 400)

    try:
        visiteur_id = require_int(data, "visiteur_id")
        motif = require_string(data, "motif", 255)
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    try:
        visiteur = Visiteur.objects.get(id=visiteur_id)
    except Visiteur.DoesNotExist:
        return json_error("Visiteur not found", 404)

    agent = get_security_personnel(request.user)
    if not agent:
        return json_error("Security personnel profile not found", 404)

    if Visite.objects.filter(visiteur=visiteur, statut="en_cours").exists():
        return json_error("Visitor already has an active visit", 400)

    visite = Visite.objects.create(
        visiteur=visiteur,
        motif=motif,
        date_entree=timezone.now(),
        date_sortie=None,
        statut="en_cours",
    )
    log_action(request.user, "create", "visiteurs.Visite", visite.id, f"entry by personnel {agent.id}", request)
    return JsonResponse(serialize_visite(visite), status=201)


@csrf_exempt
@method_required("PUT")
@require_roles("securite")
def sortie_visite(request, id):
    try:
        visite = Visite.objects.select_related("visiteur").get(id=id)
    except Visite.DoesNotExist:
        return json_error("Visit not found", 404)

    if visite.statut != "en_cours":
        return json_error("Visit already closed", 400)

    visite.date_sortie = timezone.now()
    visite.statut = "sorti"
    visite.save(update_fields=["date_sortie", "statut"])
    log_action(request.user, "update", "visiteurs.Visite", visite.id, "exit", request)
    return JsonResponse(serialize_visite(visite))
