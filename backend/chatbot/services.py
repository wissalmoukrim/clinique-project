
import logging

from django.conf import settings
from django.core.cache import cache

from consultations.models import Consultation
from facturation.models import Facture
from hospitalisation.models import Hospitalisation
from patients.models import Patient
from rendezvous.models import RendezVous

logger = logging.getLogger(__name__)

CLINIC_INFO_CACHE_KEY = "chatbot_clinic_info"
CLINIC_INFO_PATH = settings.BASE_DIR / "chatbot" / "clinic_info.txt"


SYSTEM_INSTRUCTION = """
Tu es l'assistant patient de la Clinique Medicale Elite.
Tu aides uniquement un patient authentifie avec des informations de triage, d'orientation et de suivi.
Tu peux expliquer des causes possibles, le niveau d'urgence et les prochaines etapes.
Tu ne dois jamais donner un diagnostic definitif, promettre un resultat, remplacer un medecin, ni prescrire un traitement.
Pour douleur thoracique, detresse respiratoire, signes d'AVC, perte de connaissance, saignement important, reaction allergique severe, douleur intense ou aggravation rapide, recommande une aide medicale urgente.
Utilise seulement le contexte patient fourni. Si une information n'est pas presente, dis-le clairement.
Reponds en francais simple, de facon concise et rassurante.
""".strip()


SAFE_FALLBACK_RESPONSE = (
    "Je ne peux pas contacter le service IA pour le moment. "
    "Si vos symptomes sont graves ou s'aggravent, contactez les urgences. "
    "Sinon, prenez rendez-vous avec un medecin de la clinique pour un avis medical."
)


def generate_patient_chatbot_response(user, message):
    context = build_patient_context(user)
    clinic_info = load_clinic_info()
    if not settings.GEMINI_API_KEY:
        logger.warning("Gemini chatbot unavailable: GEMINI_API_KEY is not configured")
        return SAFE_FALLBACK_RESPONSE

    try:
        response_text = call_gemini(
            contents=(
                "Reference clinique autorisee:\n"
                f"{clinic_info}\n\n"
                "Contexte patient autorise:\n"
                f"{context}\n\n"
                "Question du patient:\n"
                f"{message}"
            )
        )
        return response_text or SAFE_FALLBACK_RESPONSE
    except Exception as exc:
        logger.warning("Gemini chatbot request failed: %s", gemini_error_summary(exc))
        return SAFE_FALLBACK_RESPONSE


def load_clinic_info():
    cached = cache.get(CLINIC_INFO_CACHE_KEY)
    if cached is not None:
        return cached

    try:
        raw = CLINIC_INFO_PATH.read_bytes()
    except OSError as exc:
        logger.warning("Clinic info file could not be read: %s", exc)
        return "Informations publiques de la clinique indisponibles."

    text = _decode_clinic_info(raw)
    text = text.strip() or "Informations publiques de la clinique indisponibles."
    cache.set(CLINIC_INFO_CACHE_KEY, text, 300)
    return text


def _decode_clinic_info(raw):
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if "Ã" in text:
            try:
                repaired = text.encode("latin-1").decode("utf-8")
                if repaired.count("Ã") < text.count("Ã"):
                    return repaired
            except UnicodeError:
                pass
        return text
    return raw.decode("utf-8", errors="replace")


def call_gemini(contents):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.2,
        ),
    )
    return (getattr(response, "text", "") or "").strip()


def gemini_error_summary(exc):
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    response_json = getattr(exc, "response_json", None) or getattr(exc, "details", None) or {}
    error = response_json.get("error") if isinstance(response_json, dict) else None
    error = error if isinstance(error, dict) else {}
    status = error.get("status") or getattr(exc, "status", None) or exc.__class__.__name__
    message = error.get("message") or getattr(exc, "message", None) or str(exc)

    parts = []
    if status_code:
        parts.append(f"status_code={status_code}")
    parts.append(f"status={status}")
    parts.append(f"message={_redact_secret(message)}")
    return " ".join(parts)


def _redact_secret(value):
    value = str(value)
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if api_key:
        value = value.replace(api_key, "[REDACTED_GEMINI_API_KEY]")
    return value


def build_patient_context(user):
    try:
        patient = Patient.objects.select_related("user").get(user=user)
    except Patient.DoesNotExist:
        return "Aucun profil patient trouve pour cet utilisateur."

    sections = [
        _profile_context(patient),
        _appointments_context(patient),
        _consultations_context(patient),
        _hospitalisations_context(patient),
        _invoices_context(patient),
    ]
    return "\n\n".join(section for section in sections if section)


def _profile_context(patient):
    return "\n".join([
        "Profil patient:",
        f"- Nom: {_patient_name(patient)}",
        f"- Date de naissance: {patient.date_naissance or 'non renseignee'}",
        f"- Sexe: {patient.sexe or 'non renseigne'}",
        f"- Groupe sanguin: {patient.groupe_sanguin or 'non renseigne'}",
        f"- Allergies: {patient.allergies or 'non renseignees'}",
        f"- Antecedents: {patient.antecedents or 'non renseignes'}",
    ])


def _appointments_context(patient):
    rendezvous = (
        RendezVous.objects.filter(patient=patient)
        .select_related("medecin__user")
        .order_by("-date", "-heure")[:8]
    )
    if not rendezvous:
        return "Rendez-vous: aucun rendez-vous trouve."
    lines = ["Rendez-vous recents et a venir:"]
    for rdv in rendezvous:
        lines.append(
            "- "
            f"{rdv.date} {str(rdv.heure)[:5]} | "
            f"Dr. {_user_name(rdv.medecin.user)} | "
            f"{rdv.medecin.specialite} | statut: {rdv.statut}"
        )
    return "\n".join(lines)


def _consultations_context(patient):
    consultations = (
        Consultation.objects.filter(patient=patient)
        .select_related("medecin__user")
        .order_by("-date")[:8]
    )
    if not consultations:
        return "Consultations: aucun historique trouve."
    lines = ["Consultations recentes:"]
    for consultation in consultations:
        lines.append(
            "- "
            f"{consultation.date} | Dr. {_user_name(consultation.medecin.user)} | "
            f"diagnostic note par le medecin: {consultation.diagnostic or 'non renseigne'} | "
            f"traitement: {consultation.traitement or 'non renseigne'} | "
            f"notes: {consultation.notes or 'non renseignees'}"
        )
    return "\n".join(lines)


def _hospitalisations_context(patient):
    hospitalisations = (
        Hospitalisation.objects.filter(patient=patient)
        .select_related("chambre")
        .order_by("-date_entree")[:5]
    )
    if not hospitalisations:
        return "Hospitalisations: aucune hospitalisation trouvee."
    lines = ["Hospitalisations recentes:"]
    for hosp in hospitalisations:
        lines.append(
            "- "
            f"entree: {hosp.date_entree} | sortie: {hosp.date_sortie or 'non renseignee'} | "
            f"statut: {hosp.statut} | motif: {hosp.motif or 'non renseigne'} | "
            f"observations: {hosp.observations or 'non renseignees'} | "
            f"temperature: {hosp.temperature or 'non renseignee'} | "
            f"tension: {hosp.tension or 'non renseignee'} | "
            f"frequence cardiaque: {hosp.frequence_cardiaque or 'non renseignee'}"
        )
    return "\n".join(lines)


def _invoices_context(patient):
    factures = Facture.objects.filter(patient=patient).order_by("-date")[:8]
    if not factures:
        return "Factures: aucune facture trouvee."
    lines = ["Factures recentes:"]
    for facture in factures:
        lines.append(f"- {facture.date} | montant: {facture.montant} MAD | statut: {facture.statut}")
    return "\n".join(lines)


def _patient_name(patient):
    return _user_name(patient.user)


def _user_name(user):
    return user.get_full_name().strip() or user.username
