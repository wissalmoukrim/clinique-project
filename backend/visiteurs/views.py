from django.core.exceptions import SuspiciousOperation
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from core.permissions import method_required, require_roles
from core.utils import json_error, log_action, log_security_event, optional_string, parse_json_body, require_fields, require_int, require_string
from personnel.models import Personnel
from .models import JournalVisite, Visiteur


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
        "visiteur": str(journal.visiteur),
        "agent_securite": journal.agent_securite.user.username if journal.agent_securite else None,
        "motif": journal.motif,
        "date_entree": str(journal.date_entree),
        "date_sortie": str(journal.date_sortie) if journal.date_sortie else None,
        "statut": journal.statut,
    }


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

    try:
        agent = Personnel.objects.get(user=request.user, fonction="securite")
    except Personnel.DoesNotExist:
        return json_error("Security personnel profile not found", 404)

    journal = JournalVisite.objects.create(
        visiteur=visiteur,
        agent_securite=agent,
        motif=motif,
    )
    log_action(request.user, "create", "visiteurs.JournalVisite", journal.id, "entry", request)
    return JsonResponse({"id": journal.id, "message": "Entry saved"}, status=201)


@csrf_exempt
@method_required("POST")
@require_roles("securite")
def sortie_visiteur(request, id):
    data = parse_json_body(request)
    if data is None:
        return json_error("Invalid JSON", 400)

    try:
        date_sortie = optional_string(data, "date_sortie", 40) or timezone.now()
    except SuspiciousOperation:
        return json_error("Invalid input", 400)

    try:
        visite = JournalVisite.objects.select_related("agent_securite__user").get(id=id)
    except JournalVisite.DoesNotExist:
        return json_error("Visit log not found", 404)

    if visite.agent_securite and visite.agent_securite.user_id != request.user.id:
        log_security_event(request.user, "forbidden_access", f"forbidden visitor exit {id}", request)
        return json_error("Forbidden", 403)

    visite.date_sortie = date_sortie
    visite.statut = JournalVisite.STATUT_CHOICES[1][0]
    visite.save(update_fields=["date_sortie", "statut"])
    log_action(request.user, "update", "visiteurs.JournalVisite", visite.id, "exit", request)
    return JsonResponse({"message": "Exit saved"})


@csrf_exempt
@method_required("GET")
@require_roles("admin", "securite", "secretaire")
def journal_visites(request):
    journaux = JournalVisite.objects.select_related("visiteur", "agent_securite__user").all()
    if request.user.role == "securite":
        journaux = journaux.filter(agent_securite__user=request.user)
    return JsonResponse([serialize_journal(j) for j in journaux], safe=False)
