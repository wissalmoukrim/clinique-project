from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import os


@api_view(['POST'])
@permission_classes([AllowAny])
def chatbot_view(request):

    message = request.data.get("message", "").lower()

    file_path = os.path.join(os.path.dirname(__file__), "clinic_info.txt")

    with open(file_path, "r", encoding="utf-8") as f:
        clinic_info = f.read()

    clinic_info_lower = clinic_info.lower()

    # Bonjour
    if "bonjour" in message or "bonsoir" in message or "salut" in message:

        reply = "Bonjour 👋 Je suis là pour répondre à vos questions sur notre clinique."

    # Nom clinique
    elif "nom" in message and "clinique" in message:

        reply = "Clinique Médicale Elite"

    # Adresse
    elif "adresse" in message:

        start = clinic_info_lower.find("adresse")
        end = clinic_info_lower.find("téléphone")

        reply = clinic_info[start:end]

    # Horaires
    elif "horaire" in message or "heure" in message:

        start = clinic_info_lower.find("horaires")
        end = clinic_info_lower.find("specialites")

        reply = clinic_info[start:end]

    # Spécialités
    elif "spécialité" in message or "specialite" in message or "spécialités" in message:

        start = clinic_info_lower.find("specialites")
        end = clinic_info_lower.find("medecins cardiologie")

        reply = clinic_info[start:end]

    # Médecins
    elif "médecin" in message or "medecin" in message or "docteur" in message or "médecins" in message:

        start = clinic_info_lower.find("medecins cardiologie")
        end = clinic_info_lower.find("procedure rendez-vous")

        reply = clinic_info[start:end]

    # Rendez-vous
    elif "rendez" in message or "rdv" in message:

        start = clinic_info_lower.find("procedure rendez-vous")
        end = clinic_info_lower.find("services disponibles")

        reply = clinic_info[start:end]

    # Ambulance
    elif "ambulance" in message:

        start = clinic_info_lower.find("ambulance")
        end = clinic_info_lower.find("visiteurs")

        reply = clinic_info[start:end]

    # Contact
    elif "telephone" in message or "email" in message or "contact" in message:

        start = clinic_info_lower.find("téléphone")
        end = clinic_info_lower.find("horaires")

        reply = clinic_info[start:end]

    else:

        reply = """
Je peux répondre aux questions concernant :

• Médecins
• Spécialités
• Rendez-vous
• Services
• Ambulance
• Horaires
• Adresse
• Contact
"""

    return Response({
        "response": reply
    })