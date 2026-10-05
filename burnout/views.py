import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Avg
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ChargeTravailForm, InscriptionForm, ProfilForm, QuestionnaireForm
from .ml_model import ModeleIndisponibleError, predict_burnout
from .models import ChargeTravail, Etudiant, Questionnaire, Resultat


def accueil(request):
    return render(request, "burnout/accueil.html")


def a_propos(request):
    return render(request, "burnout/a_propos.html")


class InscriptionView(CreateView):
    form_class = InscriptionForm
    template_name = "burnout/register.html"
    success_url = reverse_lazy("burnout:dashboard")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, "Bienvenue ! Votre compte a été créé avec succès.")
        return response


class ConnexionView(LoginView):
    template_name = "burnout/login.html"
    redirect_authenticated_user = True

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()
        return form


def _get_etudiant(request):
    """Récupère le profil Étudiant du user connecté, ou lève Http404."""
    try:
        return request.user.etudiant
    except Etudiant.DoesNotExist:
        raise Http404("Aucun profil étudiant associé à ce compte.")


@login_required
def dashboard(request):
    etudiant = _get_etudiant(request)
    dernier_resultat = (
        Resultat.objects.filter(questionnaire__etudiant=etudiant).order_by("-date_creation").first()
    )
    derniere_charge = etudiant.charges_travail.order_by("-date_creation").first()

    resultats = list(
        Resultat.objects.filter(questionnaire__etudiant=etudiant).order_by("date_creation")[:20]
    )
    charges = list(etudiant.charges_travail.order_by("date_creation")[:20])

    moyennes = etudiant.charges_travail.aggregate(
        moy_etude=Avg("heures_etude_jour"),
        moy_sommeil=Avg("heures_sommeil_jour"),
        moy_repos=Avg("temps_repos_jour"),
    )

    context = {
        "etudiant": etudiant,
        "dernier_resultat": dernier_resultat,
        "derniere_charge": derniere_charge,
        "moyennes": moyennes,
        "labels_risque": json.dumps([r.date_creation.strftime("%d/%m") for r in resultats]),
        "scores_risque": json.dumps([r.score_risque for r in resultats]),
        "labels_charge": json.dumps([c.date_creation.strftime("%d/%m") for c in charges]),
        "heures_etude": json.dumps([c.heures_etude_jour for c in charges]),
        "heures_sommeil": json.dumps([c.heures_sommeil_jour for c in charges]),
        "heures_repos": json.dumps([c.temps_repos_jour for c in charges]),
    }
    return render(request, "burnout/dashboard.html", context)


@login_required
def questionnaire_view(request):
    etudiant = _get_etudiant(request)
    if request.method == "POST":
        form = QuestionnaireForm(request.POST)
        if form.is_valid():
            questionnaire = form.save(commit=False)
            questionnaire.etudiant = etudiant
            questionnaire.save()
            messages.success(request, "Questionnaire enregistré. Renseignez maintenant votre charge de travail.")
            return redirect("burnout:charge_travail", questionnaire_id=questionnaire.pk)
        messages.error(request, "Le questionnaire contient des erreurs. Veuillez vérifier vos réponses.")
    else:
        form = QuestionnaireForm()
    return render(request, "burnout/questionnaire.html", {"form": form})


@login_required
def charge_travail_view(request, questionnaire_id):
    etudiant = _get_etudiant(request)
    questionnaire = get_object_or_404(Questionnaire, pk=questionnaire_id, etudiant=etudiant)

    if hasattr(questionnaire, "resultat"):
        messages.info(request, "Ce questionnaire a déjà été analysé.")
        return redirect("burnout:resultat", resultat_id=questionnaire.resultat.pk)

    if request.method == "POST":
        form = ChargeTravailForm(request.POST)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.etudiant = etudiant
            charge.save()
            return _lancer_analyse(request, questionnaire, charge)
        messages.error(request, "Merci de corriger les erreurs du formulaire de charge de travail.")
    else:
        form = ChargeTravailForm()
    return render(request, "burnout/charge_travail.html", {"form": form, "questionnaire": questionnaire})


@login_required
def suivi_charge_travail(request):
    """Page de suivi périodique de la charge de travail (hors questionnaire)."""
    etudiant = _get_etudiant(request)
    if request.method == "POST":
        form = ChargeTravailForm(request.POST)
        if form.is_valid():
            charge = form.save(commit=False)
            charge.etudiant = etudiant
            charge.save()
            messages.success(request, "Votre charge de travail a été enregistrée.")
            return redirect("burnout:suivi_charge_travail")
    else:
        form = ChargeTravailForm()

    charges = etudiant.charges_travail.order_by("-date_creation")[:15]
    moyennes = etudiant.charges_travail.aggregate(
        moy_etude=Avg("heures_etude_jour"),
        moy_sommeil=Avg("heures_sommeil_jour"),
        moy_repos=Avg("temps_repos_jour"),
    )
    return render(request, "burnout/suivi_charge.html", {
        "form": form, "charges": charges, "moyennes": moyennes,
    })


def _lancer_analyse(request, questionnaire, charge):
    """Appelle le modèle ML et enregistre un Résultat."""
    data = {
        "stress": questionnaire.stress,
        "fatigue": questionnaire.fatigue,
        "motivation": questionnaire.motivation,
        "concentration": questionnaire.concentration,
        "sommeil": questionnaire.sommeil,
        "charge_mentale": questionnaire.charge_mentale,
        "sentiment_debordement": questionnaire.sentiment_debordement,
        "equilibre_vie_etudes": questionnaire.equilibre_vie_etudes,
        "heures_cours_semaine": charge.heures_cours_semaine,
        "heures_etude_jour": charge.heures_etude_jour,
        "heures_sommeil_jour": charge.heures_sommeil_jour,
        "nombre_devoirs": charge.nombre_devoirs,
        "nombre_projets": charge.nombre_projets,
        "nombre_examens": charge.nombre_examens,
        "nombre_echeances_semaine": charge.nombre_echeances_semaine,
        "temps_repos_jour": charge.temps_repos_jour,
    }

    try:
        prediction = predict_burnout(data)
    except ModeleIndisponibleError as exc:
        messages.error(
            request,
            "L'analyse n'a pas pu être réalisée car le modèle d'estimation n'est pas disponible. "
            "Merci de contacter l'administrateur du site.",
        )
        return redirect("burnout:dashboard")
    except (ValueError, KeyError):
        messages.error(request, "Une erreur est survenue lors de l'analyse de vos réponses.")
        return redirect("burnout:dashboard")

    resultat = Resultat.objects.create(
        questionnaire=questionnaire,
        charge_travail=charge,
        score_risque=prediction["score_risque"],
        niveau_risque=prediction["niveau_risque"],
        probabilite=prediction["probabilite"],
        facteurs_principaux=json.dumps(prediction["facteurs_principaux"], ensure_ascii=False),
        recommandation=prediction["recommandation"],
    )
    messages.success(request, "Votre estimation est disponible.")
    return redirect("burnout:resultat", resultat_id=resultat.pk)


@login_required
def resultat_view(request, resultat_id):
    etudiant = _get_etudiant(request)
    resultat = get_object_or_404(Resultat, pk=resultat_id, questionnaire__etudiant=etudiant)
    return render(request, "burnout/resultat.html", {"resultat": resultat})


@login_required
def recommandations_view(request, resultat_id):
    etudiant = _get_etudiant(request)
    resultat = get_object_or_404(Resultat, pk=resultat_id, questionnaire__etudiant=etudiant)
    return render(request, "burnout/recommandations.html", {"resultat": resultat})


@login_required
def historique_view(request):
    etudiant = _get_etudiant(request)
    resultats = Resultat.objects.filter(questionnaire__etudiant=etudiant).order_by("-date_creation")
    return render(request, "burnout/historique.html", {"resultats": resultats})


@login_required
def profil_view(request):
    etudiant = _get_etudiant(request)
    if request.method == "POST":
        form = ProfilForm(request.POST, instance=etudiant)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect("burnout:profil")
        messages.error(request, "Merci de corriger les erreurs du formulaire.")
    else:
        form = ProfilForm(instance=etudiant)
    return render(request, "burnout/profil.html", {"form": form})
