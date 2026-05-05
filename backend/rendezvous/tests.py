import json

from django.contrib.auth import authenticate, get_user_model
from django.test import Client, TestCase

from medecins.models import Medecin
from patients.models import Patient
from .models import RendezVous


User = get_user_model()


class PublicRendezVousTests(TestCase):
    def setUp(self):
        self.client = Client()
        medecin_user = User.objects.create_user(
            username="dr.cardio@example.com",
            password="test-pass",
            role="medecin",
        )
        self.medecin = Medecin.objects.create(
            user=medecin_user,
            specialite="Cardiologie",
            telephone="0600000000",
            disponible=True,
        )
        self.patient_user = User.objects.create_user(
            username="patient@example.com",
            password="test-pass",
            role="patient",
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            telephone="0622222222",
        )
        self.secretaire_user = User.objects.create_user(
            username="secretaire@example.com",
            password="test-pass",
            role="secretaire",
        )

    def post_public_rdv(self, overrides=None):
        payload = {
            "nom": "Patient Public",
            "email": "public@example.com",
            "telephone": "0611111111",
            "specialite": "Cardiologie",
            "date": "2026-05-10",
            "heure": "10:30",
        }
        payload.update(overrides or {})
        return self.client.post(
            "/api/rendezvous/",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_public_rdv_creates_patient_account_and_login_credentials(self):
        response = self.post_public_rdv()

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data["account_created"])
        self.assertEqual(data["username"], "public@example.com")
        self.assertTrue(data["password_temporaire"])

        user = User.objects.get(username="public@example.com")
        self.assertEqual(user.role, "patient")
        self.assertEqual(user.email, "public@example.com")
        self.assertEqual(user.first_name, "Patient Public")

        patient = Patient.objects.get(user=user)
        self.assertEqual(patient.telephone, "0611111111")
        self.assertTrue(RendezVous.objects.filter(patient=patient, medecin=self.medecin).exists())
        self.assertEqual(authenticate(username=user.username, password=data["password_temporaire"]), user)

    def test_public_rdv_reuses_existing_patient_account_without_new_password(self):
        user = User.objects.create_user(
            username="public@example.com",
            email="public@example.com",
            password="existing-pass",
            role="patient",
        )
        patient = Patient.objects.create(user=user, telephone="")

        response = self.post_public_rdv()

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertFalse(data["account_created"])
        self.assertNotIn("password_temporaire", data)

        patient.refresh_from_db()
        self.assertEqual(patient.telephone, "0611111111")
        self.assertEqual(User.objects.filter(username="public@example.com").count(), 1)
        self.assertEqual(RendezVous.objects.filter(patient=patient).count(), 1)

    def test_public_rdv_rejects_email_used_by_non_patient(self):
        User.objects.create_user(
            username="public@example.com",
            email="public@example.com",
            password="staff-pass",
            role="secretaire",
        )

        response = self.post_public_rdv()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Email already used by another account")
        self.assertEqual(Patient.objects.count(), 1)
        self.assertEqual(RendezVous.objects.count(), 0)

    def test_secretaire_can_update_rdv_status_with_put(self):
        rdv = RendezVous.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            date="2026-05-10",
            heure="10:30",
        )
        self.client.force_login(self.secretaire_user)

        response = self.client.put(
            f"/api/rendezvous/{rdv.id}/update-status/",
            data=json.dumps({"statut": "confirme"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["statut"], "confirme")
        rdv.refresh_from_db()
        self.assertEqual(rdv.statut, "confirme")

    def test_secretaire_cannot_confirm_two_rdvs_on_same_doctor_slot(self):
        first = RendezVous.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            date="2026-05-10",
            heure="10:30",
            statut="confirme",
        )
        second = RendezVous.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            date=first.date,
            heure=first.heure,
        )
        self.client.force_login(self.secretaire_user)

        response = self.client.put(
            f"/api/rendezvous/{second.id}/update-status/",
            data=json.dumps({"statut": "confirme"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "This appointment slot is already confirmed for this doctor")
        second.refresh_from_db()
        self.assertEqual(second.statut, "en_attente")

    def test_patient_cannot_update_rdv_status(self):
        rdv = RendezVous.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            date="2026-05-10",
            heure="10:30",
        )
        self.client.force_login(self.patient_user)

        response = self.client.put(
            f"/api/rendezvous/{rdv.id}/update-status/",
            data=json.dumps({"statut": "annule"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)
        rdv.refresh_from_db()
        self.assertEqual(rdv.statut, "en_attente")

    def test_legacy_status_endpoint_still_accepts_post_for_secretaire(self):
        rdv = RendezVous.objects.create(
            patient=self.patient,
            medecin=self.medecin,
            date="2026-05-10",
            heure="10:30",
        )
        self.client.force_login(self.secretaire_user)

        response = self.client.post(
            f"/api/rendezvous/{rdv.id}/status/",
            data=json.dumps({"statut": "annule"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["statut"], "annule")
