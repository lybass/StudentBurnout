from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .ml_model import predict_burnout
from .models import ChargeTravail, Etudiant, Questionnaire, Resultat


class InscriptionEtConnexionTests(TestCase):
    def test_inscription_cree_user_et_etudiant(self):
        response = self.client.post(reverse("burnout:register"), {
            "username": "alice",
            "email": "alice@example.com",
            "prenom": "Alice",
            "nom": "Diop",
            "formation": "MILIA",
            "niveau_etude": "Master 1",
            "universite": "EPT",
            "password1": "MotDePasseSolide123!",
            "password2": "MotDePasseSolide123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="alice").exists())
        self.assertTrue(Etudiant.objects.filter(user__username="alice").exists())

    def test_connexion_utilisateur_existant(self):
        user = User.objects.create_user(username="bob", password="MotDePasseSolide123!")
        Etudiant.objects.create(user=user, nom="Fall", prenom="Bob", email="bob@example.com")
        response = self.client.post(reverse("burnout:login"), {
            "username": "bob", "password": "MotDePasseSolide123!",
        })
        self.assertEqual(response.status_code, 302)


class PagesPriveesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="claire", password="MotDePasseSolide123!")
        self.etudiant = Etudiant.objects.create(
            user=self.user, nom="Sarr", prenom="Claire", email="claire@example.com"
        )

    def test_dashboard_protege(self):
        response = self.client.get(reverse("burnout:dashboard"))
        self.assertEqual(response.status_code, 302)  # redirigé vers login

    def test_dashboard_accessible_connecte(self):
        self.client.login(username="claire", password="MotDePasseSolide123!")
        response = self.client.get(reverse("burnout:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_historique_protege(self):
        response = self.client.get(reverse("burnout:historique"))
        self.assertEqual(response.status_code, 302)


class QuestionnaireEtAnalyseTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="david", password="MotDePasseSolide123!")
        self.etudiant = Etudiant.objects.create(
            user=self.user, nom="Ndiaye", prenom="David", email="david@example.com"
        )
        self.client.login(username="david", password="MotDePasseSolide123!")

    def test_soumission_questionnaire_valide(self):
        data = {
            "stress": 4, "fatigue": 4, "motivation": 2, "concentration": 2,
            "sentiment_debordement": 4, "sommeil": 2, "charge_mentale": 4,
            "equilibre_vie_etudes": 2, "isolement": 3, "satisfaction_etudes": 2,
        }
        response = self.client.post(reverse("burnout:questionnaire"), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Questionnaire.objects.filter(etudiant=self.etudiant).count(), 1)

    def test_questionnaire_incomplet_est_invalide(self):
        response = self.client.post(reverse("burnout:questionnaire"), {"stress": 3})
        self.assertEqual(response.status_code, 200)  # ré-affiche le formulaire
        self.assertEqual(Questionnaire.objects.count(), 0)

    def test_parcours_complet_jusqu_au_resultat(self):
        questionnaire = Questionnaire.objects.create(
            etudiant=self.etudiant, stress=4, fatigue=4, motivation=2, concentration=2,
            sentiment_debordement=4, sommeil=2, charge_mentale=4,
            equilibre_vie_etudes=2, isolement=3, satisfaction_etudes=2,
        )
        charge_data = {
            "heures_cours_semaine": 28, "heures_etude_jour": 6, "heures_sommeil_jour": 5,
            "nombre_devoirs": 6, "nombre_projets": 3, "nombre_examens": 3,
            "nombre_echeances_semaine": 8, "temps_repos_jour": 1,
        }
        response = self.client.post(
            reverse("burnout:charge_travail", args=[questionnaire.pk]), charge_data
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ChargeTravail.objects.count(), 1)
        self.assertEqual(Resultat.objects.count(), 1)

        resultat = Resultat.objects.first()
        self.assertIn(resultat.niveau_risque, ["FAIBLE", "MODERE", "ELEVE"])


class SecuriteAccesDonneesTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="etu1", password="MotDePasseSolide123!")
        self.etudiant1 = Etudiant.objects.create(user=self.user1, nom="A", prenom="A", email="a@example.com")
        self.user2 = User.objects.create_user(username="etu2", password="MotDePasseSolide123!")
        self.etudiant2 = Etudiant.objects.create(user=self.user2, nom="B", prenom="B", email="b@example.com")

        questionnaire = Questionnaire.objects.create(
            etudiant=self.etudiant1, stress=3, fatigue=3, motivation=3, concentration=3,
            sentiment_debordement=3, sommeil=3, charge_mentale=3,
            equilibre_vie_etudes=3, isolement=3, satisfaction_etudes=3,
        )
        self.resultat1 = Resultat.objects.create(
            questionnaire=questionnaire, score_risque=50, niveau_risque="MODERE",
            probabilite=60, facteurs_principaux="[]", recommandation="Test",
        )

    def test_impossible_de_consulter_resultat_d_un_autre_etudiant(self):
        self.client.login(username="etu2", password="MotDePasseSolide123!")
        response = self.client.get(reverse("burnout:resultat", args=[self.resultat1.pk]))
        self.assertEqual(response.status_code, 404)

    def test_proprietaire_peut_consulter_son_resultat(self):
        self.client.login(username="etu1", password="MotDePasseSolide123!")
        response = self.client.get(reverse("burnout:resultat", args=[self.resultat1.pk]))
        self.assertEqual(response.status_code, 200)


class PredictBurnoutTests(TestCase):
    def test_predict_burnout_retourne_un_resultat_coherent(self):
        data = {
            "stress": 5, "fatigue": 5, "motivation": 1, "concentration": 1,
            "sommeil": 1, "charge_mentale": 5, "sentiment_debordement": 5,
            "equilibre_vie_etudes": 1, "heures_cours_semaine": 35,
            "heures_etude_jour": 8, "heures_sommeil_jour": 4,
            "nombre_devoirs": 8, "nombre_projets": 4, "nombre_examens": 4,
            "nombre_echeances_semaine": 10, "temps_repos_jour": 0.5,
        }
        resultat = predict_burnout(data)
        self.assertIn(resultat["niveau_risque"], ["FAIBLE", "MODERE", "ELEVE"])
        self.assertIsInstance(resultat["facteurs_principaux"], list)
        self.assertIn("indicative", resultat["mention"])
