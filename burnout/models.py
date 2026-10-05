"""
Modèles de données de l'application StudentBurnout.

Rappel important : les résultats produits par cette application sont des
estimations indicatives basées sur des données déclaratives. Ils ne
constituent en aucun cas un diagnostic médical.
"""
from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


ECHELLE_5 = [
    (1, "1 - Très faible"),
    (2, "2 - Faible"),
    (3, "3 - Moyen"),
    (4, "4 - Élevé"),
    (5, "5 - Très élevé"),
]

NIVEAU_RISQUE_CHOICES = [
    ("FAIBLE", "Faible"),
    ("MODERE", "Modéré"),
    ("ELEVE", "Élevé"),
]


class Etudiant(models.Model):
    """Profil étudiant, lié un-à-un à un compte utilisateur Django."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="etudiant")
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField()
    formation = models.CharField(max_length=150, blank=True)
    niveau_etude = models.CharField(max_length=100, blank=True)
    universite = models.CharField(max_length=150, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Étudiant"
        verbose_name_plural = "Étudiants"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Questionnaire(models.Model):
    """Réponses déclaratives d'un étudiant sur son état général."""

    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name="questionnaires")

    # Section 1 : état général
    stress = models.IntegerField(choices=ECHELLE_5)
    fatigue = models.IntegerField(choices=ECHELLE_5)
    motivation = models.IntegerField(choices=ECHELLE_5)
    concentration = models.IntegerField(choices=ECHELLE_5)
    sentiment_debordement = models.IntegerField(choices=ECHELLE_5)

    # Section 2 : sommeil et récupération
    sommeil = models.IntegerField(choices=ECHELLE_5, help_text="Qualité perçue du sommeil")

    # Section 3 : études
    charge_mentale = models.IntegerField(choices=ECHELLE_5)

    # Section 4 : équilibre
    equilibre_vie_etudes = models.IntegerField(choices=ECHELLE_5)
    isolement = models.IntegerField(choices=ECHELLE_5)
    satisfaction_etudes = models.IntegerField(choices=ECHELLE_5)

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Questionnaire"
        verbose_name_plural = "Questionnaires"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Questionnaire de {self.etudiant} du {self.date_creation:%d/%m/%Y}"


class ChargeTravail(models.Model):
    """Suivi périodique de la charge de travail académique."""

    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name="charges_travail")

    heures_cours_semaine = models.FloatField()
    heures_etude_jour = models.FloatField()
    heures_sommeil_jour = models.FloatField()
    nombre_devoirs = models.IntegerField(default=0)
    nombre_projets = models.IntegerField(default=0)
    nombre_examens = models.IntegerField(default=0)
    nombre_echeances_semaine = models.IntegerField(default=0)
    temps_repos_jour = models.FloatField(help_text="Temps de repos/détente par jour, en heures")

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Charge de travail"
        verbose_name_plural = "Charges de travail"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Charge de travail de {self.etudiant} du {self.date_creation:%d/%m/%Y}"


class Resultat(models.Model):
    """Résultat d'une estimation de risque produite par le modèle ML."""

    questionnaire = models.OneToOneField(Questionnaire, on_delete=models.CASCADE, related_name="resultat")
    charge_travail = models.ForeignKey(ChargeTravail, on_delete=models.SET_NULL, null=True, blank=True)

    score_risque = models.FloatField(help_text="Probabilité (%) associée au niveau de risque prédit")
    niveau_risque = models.CharField(max_length=10, choices=NIVEAU_RISQUE_CHOICES)
    probabilite = models.FloatField(help_text="Probabilité (%) de la classe prédite")
    facteurs_principaux = models.TextField(help_text="Facteurs stockés en JSON (liste de chaînes)")
    recommandation = models.TextField()

    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Résultat"
        verbose_name_plural = "Résultats"
        ordering = ["-date_creation"]

    def __str__(self):
        return f"Résultat {self.niveau_risque} - {self.questionnaire.etudiant}"

    def get_absolute_url(self):
        return reverse("burnout:resultat", args=[self.pk])

    def facteurs_liste(self):
        import json
        try:
            return json.loads(self.facteurs_principaux)
        except (ValueError, TypeError):
            return []
