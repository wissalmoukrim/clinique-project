
import logging
import re
import unicodedata

from django.conf import settings
from django.core.cache import cache

from consultations.models import Consultation
from facturation.models import Facture
from hospitalisation.models import Hospitalisation
from patients.models import Patient
from rendezvous.models import RendezVous
from medecins.models import Medecin

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

PUBLIC_SYSTEM_INSTRUCTION = """
Tu es l'assistant public de la Clinique Medicale Elite.
Tu peux repondre aux questions medicales generales et aux informations publiques de la clinique: specialites, medecins, horaires, contact, localisation, procedure de rendez-vous et orientation generale.
Tu peux expliquer des symptomes possibles, des causes generales, des mesures de prudence et quand consulter, mais tu ne poses jamais de diagnostic definitif.
Tu ne prescris jamais de traitement personnalise, de dosage, ni de changement de medicament. Tu recommandes toujours de consulter un professionnel pour une decision medicale.
Pour douleur thoracique, detresse respiratoire, signes d'AVC, perte de connaissance, saignement important, reaction allergique severe, douleur intense ou aggravation rapide, recommande une aide medicale urgente.
Tu n'as jamais acces aux dossiers patients, comptes utilisateurs, JWT, factures, donnees administratives internes ou donnees medicales personnelles.
Si la question demande une donnee privee, une action admin, une extraction de base de donnees, un token, un mot de passe ou un secret, refuse poliment.
Reponds en francais simple, de facon concise et professionnelle.
""".strip()


SAFE_FALLBACK_RESPONSE = (
    "Je ne peux pas contacter le service IA pour le moment. "
    "Si vos symptomes sont graves ou s'aggravent, contactez les urgences. "
    "Sinon, prenez rendez-vous avec un medecin de la clinique pour un avis medical."
)

PUBLIC_FORBIDDEN_TOPICS = {
    "admin",
    "administrateur",
    "compte",
    "comptes",
    "dossier",
    "dossiers",
    "facture",
    "factures",
    "facturation",
    "jwt",
    "mot de passe",
    "paiement",
    "token",
    "utilisateur",
}

PUBLIC_RESPONSE_FORBIDDEN_TOPICS = {
    "admin password",
    "bearer ",
    "jwt",
    "mot de passe",
    "numero de securite",
    "password",
    "secret",
    "token",
}

PUBLIC_SPECIALTIES = {
    "cardiologie": "La cardiologie assure le suivi cardiovasculaire, la tension, l'ECG et la prevention.",
    "gynecologie": "La gynecologie propose les consultations de suivi, le depistage et l'accompagnement.",
    "pediatrie": "La pediatrie couvre les soins et le suivi medical des enfants.",
    "chirurgie generale": "La chirurgie generale concerne les avis chirurgicaux et le suivi pre et post-operatoire.",
    "radiologie": "La radiologie realise les examens d'imagerie et d'aide au diagnostic.",
    "medecine generale": "La medecine generale couvre les consultations courantes et l'orientation medicale.",
}

PUBLIC_STATIC_RESPONSES = [
    (
        {"bonjour", "salut", "hello", "bonsoir"},
        "Bonjour. Je peux vous aider avec les specialites, les medecins, les horaires, le contact, la localisation et la prise de rendez-vous.",
    ),
    (
        {"horaire", "horaires", "ouvert", "ouverture", "fermeture"},
        "La Clinique Medicale Elite est ouverte 24h/24, tous les jours. Les urgences sont orientees en priorite vers l'accueil.",
    ),
    (
        {"contact", "telephone", "tel", "email", "mail", "appeler"},
        "Vous pouvez contacter la clinique au +212 522 000 000 ou par email a contact@clinique-elite.ma.",
    ),
    (
        {"adresse", "localisation", "localiser", "situe", "ou etes vous", "plan"},
        "La clinique se situe Avenue de la Sante, Casablanca.",
    ),
    (
        {"rdv", "rendez vous", "rendez-vous", "reservation", "prendre"},
        "Pour prendre rendez-vous, ouvrez la page Prendre RDV, choisissez une specialite, un medecin, une date et une heure.",
    ),
    (
        {"urgence", "urgent", "ambulance"},
        "En cas d'urgence, contactez immediatement l'accueil ou les services d'urgence locaux. Les ambulances de la clinique sont disponibles 24h/24.",
    ),
]

PUBLIC_FALLBACK_RESPONSE = (
    "Je peux repondre aux questions medicales generales et aux informations publiques de la clinique. Pour une urgence ou un avis personnalise, contactez un professionnel de sante."
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


def generate_public_chatbot_response(message):
    text = normalize_public_message(message)
    if not text:
        return PUBLIC_STATIC_RESPONSES[0][1]

    if contains_public_forbidden_topic(text):
        return "Je ne peux pas acceder aux dossiers patients, comptes, factures, consultations, hospitalisations, donnees JWT ou informations administratives."

    for keywords, response in PUBLIC_STATIC_RESPONSES:
        if any(keyword in text for keyword in keywords):
            return response

    if "special" in text or any(specialty in text for specialty in PUBLIC_SPECIALTIES):
        return public_specialties_response(text)

    if "medecin" in text or "docteur" in text or "docteurs" in text or "docteur" in text:
        return public_doctors_response(text)

    return generate_public_gemini_response(message)


def generate_public_gemini_response(message):
    fallback = PUBLIC_FALLBACK_RESPONSE
    if not settings.GEMINI_API_KEY:
        logger.warning("Public Gemini chatbot unavailable: GEMINI_API_KEY is not configured")
        return fallback

    try:
        response_text = call_gemini(
            contents=(
                "Contexte public autorise:\n"
                f"{build_public_clinic_context()}\n\n"
                "Question du visiteur:\n"
                f"{message}"
            ),
            system_instruction=PUBLIC_SYSTEM_INSTRUCTION,
        )
    except Exception as exc:
        logger.warning("Public Gemini chatbot request failed: %s", gemini_error_summary(exc))
        return fallback

    response_text = (response_text or "").strip()
    if not response_text:
        return fallback

    normalized_response = normalize_public_message(response_text)
    if any(topic in normalized_response for topic in PUBLIC_RESPONSE_FORBIDDEN_TOPICS):
        return "Je peux vous aider avec les informations publiques de la clinique, mais je ne peux pas fournir de donnees privees ou medicales sensibles."

    return response_text


def build_public_clinic_context():
    return "\n\n".join([
        public_general_clinic_context(),
        public_specialties_context(),
        public_doctors_context(),
    ])


def public_general_clinic_context():
    return "\n".join([
        "CLINIQUE MEDICALE ELITE",
        "Adresse publique: Avenue de la Sante, Casablanca.",
        "Telephone public: +212 522 000 000.",
        "Email public: contact@clinique-elite.ma.",
        "Horaires publics: ouvert 24h/24, tous les jours.",
        "Procedure publique de rendez-vous: le visiteur choisit une specialite, un medecin, une date et une heure sur la page Prendre RDV.",
        "Domaines autorises dans les reponses: questions medicales generales, specialites medicales, medecins disponibles, horaires, contact, localisation et prise de rendez-vous.",
        "Limite medicale: pas de diagnostic definitif, pas de prescription personnalisee, pas de donnees medicales personnelles.",
    ])


def public_specialties_context():
    lines = ["Specialites publiques:"]
    for specialty, description in PUBLIC_SPECIALTIES.items():
        lines.append(f"- {specialty}: {description}")
    return "\n".join(lines)


def public_doctors_context():
    medecins = Medecin.objects.filter(disponible=True).select_related("user").order_by("specialite", "user__first_name", "user__username")[:30]
    lines = ["Medecins publics disponibles:"]
    for medecin in medecins:
        name = medecin.user.get_full_name().strip() or medecin.user.username
        experience = f", {medecin.experience} ans d'experience" if medecin.experience else ""
        lines.append(f"- Dr. {name}: {medecin.specialite}{experience}")
    if len(lines) == 1:
        lines.append("- Aucun medecin public disponible dans la base pour le moment.")
    return "\n".join(lines)


def normalize_public_message(message):
    text = str(message or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = re.sub(r"\s+", " ", text)
    return text


def contains_public_forbidden_topic(text):
    return any(topic in text for topic in PUBLIC_FORBIDDEN_TOPICS)


def public_specialties_response(text):
    matched = [label for key, label in PUBLIC_SPECIALTIES.items() if key in text]
    if matched:
        return " ".join(matched)
    return "Specialites publiques disponibles: " + ", ".join(sorted(PUBLIC_SPECIALTIES.keys())) + "."


def public_doctors_response(text):
    medecins = Medecin.objects.filter(disponible=True).select_related("user").order_by("specialite", "user__first_name", "user__username")
    doctors = []
    for medecin in medecins[:20]:
        specialty = normalize_public_message(medecin.specialite)
        if any(key in text for key in PUBLIC_SPECIALTIES) and specialty not in text:
            continue
        name = medecin.user.get_full_name().strip() or medecin.user.username
        doctors.append(f"Dr. {name} ({medecin.specialite})")

    if doctors:
        return "Medecins disponibles: " + ", ".join(doctors) + "."

    return "Les medecins publics sont consultables sur la page Medecins. Vous pouvez aussi choisir une specialite sur la page Prendre RDV."


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


def call_gemini(contents, system_instruction=SYSTEM_INSTRUCTION):
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
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
