import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from facturation.models import Facture
from medecins.models import Medecin
from patients.models import Patient
from rendezvous.models import RendezVous
from .models import Consultation


User = get_user_model()


class ConsultationBusinessRulesTests(TestCase):
    def setUp(self):
        self.medecin_user = User.objects.create_user(username="dr-a", password="pass", role="medecin")
        self.other_medecin_user = User.objects.create_user(username="dr-b", password="pass", role="medecin")
        self.patient_user = User.objects.create_user(username="patient-a", password="pass", role="patient")
        self.secretary_user = User.objects.create_user(username="sec", password="pass", role="secretaire")

        self.medecin = Medecin.objects.create(user=self.medecin_user, specialite="Cardiologie")
        self.other_medecin = Medecin.objects.create(user=self.other_medecin_user, specialite="Dermatologie")
        self.patient = Patient.objects.create(user=self.patient_user)

        self.confirmed_rdv = RendezVous.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            date="2026-05-02",
            heure="09:30",
            statut="confirme",
        )
        self.pending_rdv = RendezVous.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            date="2026-05-03",
            heure="10:30",
            statut="en_attente",
        )

    def post_consultation(self, user, rdv, diagnostic="Diagnostic test"):
        self.client.force_login(user)
        return self.client.post(
            "/api/consultations/",
            data=json.dumps({
                "rdv_id": rdv.id,
                "diagnostic": diagnostic,
                "notes": "Notes cliniques",
                "traitement": "Traitement",
            }),
            content_type="application/json",
        )

    def test_medecin_can_create_consultation_for_confirmed_owned_rdv(self):
        response = self.post_consultation(self.medecin_user, self.confirmed_rdv)

        self.assertEqual(response.status_code, 201)
        consultation = Consultation.objects.get(rendezvous=self.confirmed_rdv)
        self.assertEqual(consultation.patient, self.patient)
        self.assertEqual(consultation.medecin, self.medecin)
        self.assertEqual(consultation.notes, "Notes cliniques")
        self.confirmed_rdv.refresh_from_db()
        self.assertEqual(self.confirmed_rdv.statut, "termine")
        facture = Facture.objects.get(consultation=consultation)
        self.assertEqual(facture.patient, self.patient)
        self.assertEqual(facture.statut, "impaye")

    def test_non_medecin_cannot_create_consultation(self):
        response = self.post_consultation(self.secretary_user, self.confirmed_rdv)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Consultation.objects.exists())

    def test_consultation_requires_confirmed_rdv(self):
        response = self.post_consultation(self.medecin_user, self.pending_rdv)

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Consultation.objects.exists())

    def test_medecin_cannot_create_consultation_for_another_medecin_rdv(self):
        response = self.post_consultation(self.other_medecin_user, self.confirmed_rdv)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Consultation.objects.exists())

    def test_only_one_consultation_per_rdv(self):
        first = self.post_consultation(self.medecin_user, self.confirmed_rdv)
        second = self.post_consultation(self.medecin_user, self.confirmed_rdv, diagnostic="Deuxieme")

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 400)
        self.assertEqual(second.json()["error"], "Consultation already exists for this appointment")
        self.assertEqual(Consultation.objects.count(), 1)

    def test_patient_can_read_own_consultations(self):
        Consultation.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            rendezvous=self.confirmed_rdv,
            diagnostic="Diagnostic visible",
            notes="Historique",
            traitement="Traitement visible",
        )
        self.client.force_login(self.patient_user)

        response = self.client.get("/api/consultations/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["diagnostic"], "Diagnostic visible")
        self.assertEqual(data[0]["notes"], "Historique")
