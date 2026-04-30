from medecins.models import Medecin


FORBIDDEN_TOPICS = {
    "patient",
    "patients",
    "facture",
    "facturation",
    "paiement",
    "consultation",
    "consultations",
    "diagnostic",
    "ordonnance",
    "hospitalisation",
}


def public_chatbot_response(message):
    text = (message or "").strip().lower()

    if not text:
        return "Bonjour. Je peux donner des informations publiques sur la clinique, les specialites et les medecins disponibles."

    if any(topic in text for topic in FORBIDDEN_TOPICS):
        return "Je ne peux pas acceder aux donnees medicales, patients, consultations ou facturation."

    if "special" in text:
        specialites = (
            Medecin.objects.filter(disponible=True)
            .exclude(specialite="")
            .values_list("specialite", flat=True)
            .distinct()
            .order_by("specialite")
        )
        values = list(specialites)
        if not values:
            return "Aucune specialite publique n'est disponible pour le moment."
        return "Specialites disponibles: " + ", ".join(values)

    if "medecin" in text or "docteur" in text:
        medecins = (
            Medecin.objects.filter(disponible=True)
            .select_related("user")
            .order_by("user__username")[:20]
        )
        values = [f"{m.user.username} ({m.specialite})" for m in medecins]
        if not values:
            return "Aucun medecin disponible n'est publie pour le moment."
        return "Medecins disponibles: " + ", ".join(values)

    if "horaire" in text or "adresse" in text or "contact" in text:
        return "Pour les informations generales, veuillez contacter l'accueil de la clinique."

    return "Je peux repondre uniquement avec des informations publiques: specialites, medecins disponibles et informations generales."
