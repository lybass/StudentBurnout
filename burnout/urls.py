from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "burnout"

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("a-propos/", views.a_propos, name="a_propos"),

    path("register/", views.InscriptionView.as_view(), name="register"),
    path("login/", views.ConnexionView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="burnout:accueil"), name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("questionnaire/", views.questionnaire_view, name="questionnaire"),
    path("charge-travail/<int:questionnaire_id>/", views.charge_travail_view, name="charge_travail"),
    path("suivi-charge/", views.suivi_charge_travail, name="suivi_charge_travail"),
    path("resultat/<int:resultat_id>/", views.resultat_view, name="resultat"),
    path("recommandations/<int:resultat_id>/", views.recommandations_view, name="recommandations"),
    path("historique/", views.historique_view, name="historique"),
    path("profil/", views.profil_view, name="profil"),
]
