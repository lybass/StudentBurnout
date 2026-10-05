from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import ChargeTravail, Etudiant, Questionnaire


class InscriptionForm(UserCreationForm):
    """Formulaire d'inscription : crée un User Django + un profil Étudiant."""

    email = forms.EmailField(required=True, label="Adresse e-mail")
    prenom = forms.CharField(max_length=100, label="Prénom")
    nom = forms.CharField(max_length=100, label="Nom")
    formation = forms.CharField(max_length=150, required=False, label="Formation")
    niveau_etude = forms.CharField(max_length=100, required=False, label="Niveau d'étude")
    universite = forms.CharField(max_length=150, required=False, label="Université")

    class Meta:
        model = User
        fields = ["username", "email", "prenom", "nom", "formation", "niveau_etude", "universite",
                  "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing + " form-control").strip()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            Etudiant.objects.create(
                user=user,
                nom=self.cleaned_data["nom"],
                prenom=self.cleaned_data["prenom"],
                email=self.cleaned_data["email"],
                formation=self.cleaned_data.get("formation", ""),
                niveau_etude=self.cleaned_data.get("niveau_etude", ""),
                universite=self.cleaned_data.get("universite", ""),
            )
        return user


class ProfilForm(forms.ModelForm):
    """Modification du profil étudiant."""

    class Meta:
        model = Etudiant
        fields = ["prenom", "nom", "email", "formation", "niveau_etude", "universite"]
        widgets = {
            "prenom": forms.TextInput(attrs={"class": "form-control"}),
            "nom": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "formation": forms.TextInput(attrs={"class": "form-control"}),
            "niveau_etude": forms.TextInput(attrs={"class": "form-control"}),
            "universite": forms.TextInput(attrs={"class": "form-control"}),
        }


ECHELLE_WIDGET = forms.RadioSelect


class QuestionnaireForm(forms.ModelForm):
    """Formulaire du questionnaire d'état, organisé en 4 sections dans le template."""

    class Meta:
        model = Questionnaire
        fields = [
            "stress", "fatigue", "motivation", "concentration", "sentiment_debordement",
            "sommeil",
            "charge_mentale",
            "equilibre_vie_etudes", "isolement", "satisfaction_etudes",
        ]
        widgets = {field: ECHELLE_WIDGET(attrs={"class": "echelle-radio"}) for field in fields}
        labels = {
            "stress": "Niveau de stress ressenti",
            "fatigue": "Niveau de fatigue",
            "motivation": "Niveau de motivation",
            "concentration": "Capacité de concentration",
            "sentiment_debordement": "Sentiment d'être débordé(e)",
            "sommeil": "Qualité perçue du sommeil",
            "charge_mentale": "Charge mentale ressentie",
            "equilibre_vie_etudes": "Équilibre entre études et vie personnelle",
            "isolement": "Sentiment d'isolement",
            "satisfaction_etudes": "Satisfaction vis-à-vis des études",
        }
        help_texts = {
            "stress": "1 = très faible stress, 5 = stress très élevé",
            "fatigue": "1 = pas de fatigue, 5 = épuisement important",
            "motivation": "1 = très faible motivation, 5 = motivation très élevée",
            "concentration": "1 = grande difficulté à se concentrer, 5 = concentration excellente",
            "sentiment_debordement": "1 = jamais débordé(e), 5 = très souvent débordé(e)",
            "sommeil": "1 = sommeil très mauvais, 5 = sommeil excellent",
            "charge_mentale": "1 = charge mentale très faible, 5 = charge mentale très élevée",
            "equilibre_vie_etudes": "1 = déséquilibre important, 5 = très bon équilibre",
            "isolement": "1 = jamais isolé(e), 5 = isolement fréquent",
            "satisfaction_etudes": "1 = très insatisfait(e), 5 = très satisfait(e)",
        }


class ChargeTravailForm(forms.ModelForm):
    """Formulaire de suivi de la charge de travail."""

    class Meta:
        model = ChargeTravail
        fields = [
            "heures_cours_semaine", "heures_etude_jour", "heures_sommeil_jour",
            "nombre_devoirs", "nombre_projets", "nombre_examens",
            "nombre_echeances_semaine", "temps_repos_jour",
        ]
        widgets = {field: forms.NumberInput(attrs={"class": "form-control", "min": 0, "step": "0.5"})
                   for field in fields}
        labels = {
            "heures_cours_semaine": "Heures de cours par semaine",
            "heures_etude_jour": "Heures d'étude par jour",
            "heures_sommeil_jour": "Heures de sommeil par jour",
            "nombre_devoirs": "Nombre de devoirs en cours",
            "nombre_projets": "Nombre de projets en cours",
            "nombre_examens": "Nombre d'examens à venir",
            "nombre_echeances_semaine": "Nombre d'échéances cette semaine",
            "temps_repos_jour": "Temps de repos/détente par jour (heures)",
        }

    def clean(self):
        cleaned_data = super().clean()
        heures_etude = cleaned_data.get("heures_etude_jour") or 0
        heures_sommeil = cleaned_data.get("heures_sommeil_jour") or 0
        heures_repos = cleaned_data.get("temps_repos_jour") or 0
        if heures_etude + heures_sommeil + heures_repos > 24:
            raise forms.ValidationError(
                "La somme des heures d'étude, de sommeil et de repos ne peut pas dépasser 24h par jour."
            )
        return cleaned_data
