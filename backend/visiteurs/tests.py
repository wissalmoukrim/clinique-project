import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from personnel.models import Personnel
from .models import Visite, Visiteur


User = get_user_model()


class VisiteurAccessControlTests(TestCase):
    def setUp(self):
        self.security_user = User.objects.create_user(username="sec", password="pass", role="securite")
        self.patient_user = User.objects.create_user(username="patient", password="pass", role="patient")
        self.security = Personnel.objects.create(user=self.security_user, fonction="securite")
        self.visiteur = Visiteur.objects.create(nom="Nom", prenom="Prenom", cin="AA123")

    def test_security_entry_creates_active_visit(self):
        self.client.force_login(self.security_user)

        response = self.client.post(
            "/api/visites/entree/",
            data=json.dumps({"visiteur_id": self.visiteur.id, "motif": "Visite patient"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        visite = Visite.objects.get(id=response.json()["id"])
        self.assertEqual(visite.statut, "en_cours")
        self.assertEqual(visite.motif, "Visite patient")
        self.assertIsNotNone(visite.date_entree)
        self.assertIsNone(visite.date_sortie)

    def test_put_sortie_closes_active_visit(self):
        visite = Visite.objects.create(
            visiteur=self.visiteur,
            motif="Visite patient",
            statut="en_cours",
        )
        self.client.force_login(self.security_user)

        response = self.client.put(f"/api/visites/{visite.id}/sortie/")

        self.assertEqual(response.status_code, 200)
        visite.refresh_from_db()
        self.assertEqual(visite.statut, "sorti")
        self.assertIsNotNone(visite.date_sortie)

    def test_only_security_can_close_visit(self):
        visite = Visite.objects.create(
            visiteur=self.visiteur,
            motif="Visite patient",
            statut="en_cours",
        )
        self.client.force_login(self.patient_user)

        response = self.client.put(f"/api/visites/{visite.id}/sortie/")

        self.assertEqual(response.status_code, 403)
        visite.refresh_from_db()
        self.assertEqual(visite.statut, "en_cours")

    def test_active_entry_is_unique_per_visitor(self):
        Visite.objects.create(
            visiteur=self.visiteur,
            motif="Visite patient",
            statut="en_cours",
        )
        self.client.force_login(self.security_user)

        response = self.client.post(
            "/api/visites/entree/",
            data=json.dumps({"visiteur_id": self.visiteur.id, "motif": "Visite patient"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "Visitor already has an active visit")

    def test_security_personnel_profile_is_created_when_missing(self):
        Personnel.objects.filter(user=self.security_user).delete()
        self.client.force_login(self.security_user)

        response = self.client.post(
            "/api/visites/entree/",
            data=json.dumps({"visiteur_id": self.visiteur.id, "motif": "Controle"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Personnel.objects.filter(user=self.security_user, fonction="securite").exists())

    def test_presents_endpoint_returns_only_active_visits(self):
        active = Visite.objects.create(visiteur=self.visiteur, motif="Active", statut="en_cours")
        Visite.objects.create(visiteur=self.visiteur, motif="Closed", statut="sorti")
        self.client.force_login(self.security_user)

        response = self.client.get("/api/visites/presents/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], active.id)
