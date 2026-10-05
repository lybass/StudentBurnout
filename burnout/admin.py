from django.contrib import admin

from .models import ChargeTravail, Etudiant, Questionnaire, Resultat


@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ("prenom", "nom", "email", "formation", "universite", "date_creation")
    search_fields = ("prenom", "nom", "email", "user__username")
    list_filter = ("formation", "niveau_etude", "universite")
    ordering = ("-date_creation",)


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "stress", "fatigue", "sommeil", "sentiment_debordement", "date_creation")
    search_fields = ("etudiant__prenom", "etudiant__nom")
    list_filter = ("date_creation",)
    ordering = ("-date_creation",)


@admin.register(ChargeTravail)
class ChargeTravailAdmin(admin.ModelAdmin):
    list_display = ("etudiant", "heures_etude_jour", "heures_sommeil_jour",
                     "nombre_devoirs", "nombre_projets", "nombre_examens", "date_creation")
    search_fields = ("etudiant__prenom", "etudiant__nom")
    list_filter = ("date_creation",)
    ordering = ("-date_creation",)


@admin.register(Resultat)
class ResultatAdmin(admin.ModelAdmin):
    list_display = ("questionnaire", "niveau_risque", "score_risque", "probabilite", "date_creation")
    search_fields = ("questionnaire__etudiant__prenom", "questionnaire__etudiant__nom")
    list_filter = ("niveau_risque", "date_creation")
    ordering = ("-date_creation",)
