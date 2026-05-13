from datetime import date, time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from consultations.models import Consultation, Medicament, Ordonnance
from facturation.models import Facture, Paiement
from hospitalisation.models import Chambre, Hospitalisation
from medecins.models import Medecin
from patients.models import Patient
from personnel.models import Personnel
from rendezvous.models import RendezVous
from visiteurs.models import JournalVisite, Visiteur
from ambulance.models import Ambulance, MissionAmbulance


DEMO_PASSWORD = "DemoPass123!"

DEMO_USERS = [
    {
        "username": "admin.demo@clinique.test",
        "role": "admin",
        "first_name": "Admin",
        "last_name": "Demo",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "username": "medecin.demo@clinique.test",
        "role": "medecin",
        "first_name": "Sara",
        "last_name": "Medecin",
    },
    {
        "username": "patient.demo@clinique.test",
        "role": "patient",
        "first_name": "Yasmine",
        "last_name": "Patient",
    },
    {
        "username": "secretaire.demo@clinique.test",
        "role": "secretaire",
        "first_name": "Nadia",
        "last_name": "Secretaire",
    },
    {
        "username": "infirmier.demo@clinique.test",
        "role": "infirmier",
        "first_name": "Amine",
        "last_name": "Infirmier",
    },
    {
        "username": "comptable.demo@clinique.test",
        "role": "comptable",
        "first_name": "Karim",
        "last_name": "Comptable",
    },
    {
        "username": "securite.demo@clinique.test",
        "role": "securite",
        "first_name": "Hassan",
        "last_name": "Securite",
    },
    {
        "username": "chauffeur.demo@clinique.test",
        "role": "chauffeur",
        "first_name": "Rachid",
        "last_name": "Chauffeur",
    },
]


class Command(BaseCommand):
    help = "Seed demo accounts for every application role."

    @transaction.atomic
    def handle(self, *args, **options):
        users = {item["role"]: self._upsert_user(item) for item in DEMO_USERS}

        medecin = self._upsert_medecin(users["medecin"])
        patient = self._upsert_patient(users["patient"])
        personnel = {
            role: self._upsert_personnel(users[role], role)
            for role in ["secretaire", "infirmier", "comptable", "securite", "chauffeur"]
        }

        rdv = self._upsert_rendezvous(patient, medecin)
        consultation = self._upsert_consultation(patient, medecin, rdv)
        self._upsert_ordonnance(consultation)
        facture = self._upsert_facture(patient, consultation)
        self._upsert_paid_facture(patient)
        self._upsert_hospitalisation(patient, consultation)
        self._upsert_security_demo(personnel["securite"])
        self._upsert_ambulance_demo(personnel["chauffeur"])

        self.stdout.write(self.style.SUCCESS("Demo users seeded successfully."))
        self.stdout.write("")
        self.stdout.write("Email / password:")
        for item in DEMO_USERS:
            self.stdout.write(f"{item['role']}: {item['username']} / {DEMO_PASSWORD}")

    def _upsert_user(self, item):
        user, _ = User.objects.update_or_create(
            username=item["username"],
            defaults={
                "email": item["username"],
                "role": item["role"],
                "first_name": item["first_name"],
                "last_name": item["last_name"],
                "is_staff": item.get("is_staff", False),
                "is_superuser": item.get("is_superuser", False),
                "is_active": True,
                "is_locked": False,
                "login_attempts": 0,
                "last_failed_login": None,
            },
        )
        user.set_password(DEMO_PASSWORD)
        user.save(update_fields=[
            "password",
            "email",
            "role",
            "first_name",
            "last_name",
            "is_staff",
            "is_superuser",
            "is_active",
            "is_locked",
            "login_attempts",
            "last_failed_login",
        ])
        return user

    def _upsert_medecin(self, user):
        medecin, _ = Medecin.objects.update_or_create(
            user=user,
            defaults={
                "specialite": "Cardiologie",
                "telephone": "+212600000101",
                "numero_ordre": "DEMO-MED-001",
                "disponible": True,
                "experience": 10,
            },
        )
        return medecin

    def _upsert_patient(self, user):
        patient, _ = Patient.objects.update_or_create(
            user=user,
            defaults={
                "telephone": "+212600000202",
                "adresse": "Casablanca",
                "date_naissance": date(1994, 5, 17),
                "sexe": "F",
                "groupe_sanguin": "O+",
                "allergies": "Penicilline",
                "antecedents": "Asthme leger",
            },
        )
        return patient

    def _upsert_personnel(self, user, role):
        personnel, _ = Personnel.objects.update_or_create(
            user=user,
            defaults={
                "fonction": role,
                "telephone": f"+212600000{300 + len(role)}",
                "adresse": "Clinique Medicale Elite",
                "actif": True,
            },
        )
        return personnel

    def _upsert_rendezvous(self, patient, medecin):
        rdv, _ = RendezVous.objects.update_or_create(
            patient=patient,
            medecin=medecin,
            date=timezone.localdate() + timedelta(days=3),
            heure=time(10, 30),
            defaults={"statut": "confirme"},
        )
        return rdv

    def _upsert_consultation(self, patient, medecin, rdv):
        consultation, _ = Consultation.objects.update_or_create(
            rendezvous=rdv,
            defaults={
                "patient": patient,
                "medecin": medecin,
                "diagnostic": "Controle asthme leger, etat stable",
                "traitement": "Suivi medical et inhalateur selon prescription du medecin",
                "notes": "Patient signale toux occasionnelle, pas de detresse respiratoire.",
            },
        )
        return consultation

    def _upsert_ordonnance(self, consultation):
        ordonnance, _ = Ordonnance.objects.update_or_create(
            consultation=consultation,
            defaults={"notes": "Ordonnance demo pour test patient."},
        )
        Medicament.objects.update_or_create(
            ordonnance=ordonnance,
            nom="Salbutamol demo",
            defaults={
                "dosage": "100 mcg",
                "frequence": "Selon prescription",
                "duree": "7 jours",
            },
        )

    def _upsert_facture(self, patient, consultation):
        facture, _ = Facture.objects.update_or_create(
            patient=patient,
            consultation=consultation,
            defaults={"montant": "300.00", "statut": "impaye"},
        )
        return facture

    def _upsert_paid_facture(self, patient):
        facture, _ = Facture.objects.update_or_create(
            patient=patient,
            consultation=None,
            hospitalisation=None,
            montant="150.00",
            defaults={"statut": "paye"},
        )
        Paiement.objects.update_or_create(
            facture=facture,
            defaults={"montant": facture.montant, "mode": "carte"},
        )

    def _upsert_hospitalisation(self, patient, consultation):
        chambre, _ = Chambre.objects.update_or_create(
            numero="D101",
            defaults={"type": "simple", "disponible": False},
        )
        Hospitalisation.objects.update_or_create(
            consultation=consultation,
            defaults={
                "patient": patient,
                "chambre": chambre,
                "date_entree": timezone.localdate() - timedelta(days=1),
                "date_sortie": None,
                "motif": "Observation respiratoire demo",
                "observations": "Etat stable, surveillance simple.",
                "temperature": "37.0",
                "tension": "12/8",
                "frequence_cardiaque": "78",
                "statut": "en_cours",
            },
        )

    def _upsert_security_demo(self, agent):
        visiteur, _ = Visiteur.objects.update_or_create(
            cin="DEMO-CIN-001",
            defaults={
                "nom": "Visiteur",
                "prenom": "Demo",
                "telephone": "+212600000901",
            },
        )
        JournalVisite.objects.update_or_create(
            visiteur=visiteur,
            agent_securite=agent,
            defaults={"motif": "Visite patient demo", "statut": "en_cours"},
        )

    def _upsert_ambulance_demo(self, chauffeur):
        ambulance, _ = Ambulance.objects.update_or_create(
            matricule="AMB-DEMO-001",
            defaults={"type": "standard", "disponible": True, "chauffeur": chauffeur},
        )
        MissionAmbulance.objects.update_or_create(
            ambulance=ambulance,
            chauffeur=chauffeur,
            patient_nom="Yasmine Patient",
            defaults={
                "lieu_depart": "Domicile demo",
                "lieu_arrivee": "Clinique Medicale Elite",
                "statut": "en_attente",
            },
        )
