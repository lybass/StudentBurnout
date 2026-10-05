"""
Intégration du modèle de Machine Learning dans l'application Django.

Charge le modèle entraîné (ml/burnout_model.pkl) et expose la fonction
predict_burnout(data) utilisée par les vues pour produire une estimation
du niveau de risque à partir des réponses d'un étudiant.
"""
import json
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(settings.BASE_DIR, "ml", "burnout_model.pkl")

_model_cache = None
_load_error = None


class ModeleIndisponibleError(Exception):
    """Levée lorsque le modèle ML n'a pas pu être chargé."""


def _load_model():
    """Charge (et met en cache) le modèle depuis le disque."""
    global _model_cache, _load_error

    if _model_cache is not None:
        return _model_cache
    if _load_error is not None:
        raise ModeleIndisponibleError(_load_error)

    try:
        import joblib
    except ImportError as exc:
        _load_error = "La bibliothèque joblib n'est pas installée."
        logger.error(_load_error)
        raise ModeleIndisponibleError(_load_error) from exc

    if not os.path.exists(MODEL_PATH):
        _load_error = (
            "Le modèle ML est introuvable (ml/burnout_model.pkl). "
            "Lancez 'python ml/train_model.py' pour l'entraîner."
        )
        logger.error(_load_error)
        raise ModeleIndisponibleError(_load_error)

    try:
        _model_cache = joblib.load(MODEL_PATH)
    except Exception as exc:  # noqa: BLE001 - on veut capturer toute erreur de chargement
        _load_error = f"Erreur lors du chargement du modèle ML : {exc}"
        logger.exception(_load_error)
        raise ModeleIndisponibleError(_load_error) from exc

    return _model_cache


# Libellés compréhensibles pour chaque variable, utilisés pour présenter les
# facteurs principaux à l'étudiant de façon lisible.
LIBELLES_FACTEURS = {
    "stress": "Niveau de stress élevé",
    "fatigue": "Fatigue importante",
    "motivation": "Motivation en baisse",
    "concentration": "Difficultés de concentration",
    "sommeil": "Sommeil de qualité insuffisante",
    "charge_mentale": "Charge mentale élevée",
    "sentiment_debordement": "Sentiment fréquent d'être débordé(e)",
    "equilibre_vie_etudes": "Déséquilibre entre études et vie personnelle",
    "heures_cours_semaine": "Volume horaire de cours élevé",
    "heures_etude_jour": "Temps d'étude quotidien élevé",
    "heures_sommeil_jour": "Temps de sommeil quotidien faible",
    "nombre_devoirs": "Nombre de devoirs important",
    "nombre_projets": "Nombre de projets important",
    "nombre_examens": "Nombre d'examens à venir important",
    "nombre_echeances_semaine": "Nombre d'échéances élevé cette semaine",
    "temps_repos_jour": "Temps de repos quotidien insuffisant",
}

# Pour ces variables, une valeur BASSE est défavorable (ex : peu de sommeil).
# On l'utilise pour décider si un facteur "faible" doit être signalé.
SENS_INVERSE = {"sommeil", "motivation", "concentration", "equilibre_vie_etudes",
                 "heures_sommeil_jour", "temps_repos_jour"}

RECOMMANDATIONS = {
    "FAIBLE": [
        "Continuez à maintenir une organisation régulière de votre travail.",
        "Conservez des périodes de repos et de sommeil suffisantes.",
        "Surveillez l'évolution de votre charge de travail dans le temps.",
    ],
    "MODERE": [
        "Réorganisez vos priorités et répartissez les tâches sur la semaine.",
        "Augmentez si possible vos temps de récupération.",
        "Surveillez particulièrement la qualité et la durée de votre sommeil.",
        "Évitez les périodes de travail excessivement longues sans pause.",
    ],
    "ELEVE": [
        "Essayez de réduire, si possible, la surcharge de travail actuelle.",
        "Prévoyez des périodes de récupération régulières.",
        "Parlez-en à un enseignant ou à un responsable pédagogique.",
        "Consultez un professionnel de santé si les difficultés persistent ou s'intensifient.",
    ],
}

MENTION_INDICATIVE = (
    "Cette estimation est indicative et ne constitue pas un diagnostic médical."
)


def predict_burnout(data: dict) -> dict:
    """
    Prédit le niveau de risque de burnout à partir des réponses fournies.

    Args:
        data: dictionnaire contenant toutes les variables listées dans
            ml/train_model.py::FEATURES.

    Returns:
        dict avec les clés : niveau_risque, probabilite, score_risque,
        facteurs_principaux (liste), recommandation (texte), mention.

    Raises:
        ModeleIndisponibleError: si le modèle n'a pas pu être chargé.
    """
    payload = _load_model()
    model = payload["model"]
    features = payload["features"]

    try:
        ligne = [float(data[f]) for f in features]
    except KeyError as exc:
        raise ValueError(f"Donnée manquante pour la prédiction : {exc}") from exc

    import pandas as pd
    X = pd.DataFrame([ligne], columns=features)

    classe_predite = model.predict(X)[0]

    probabilite = None
    score_risque = None
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X)[0]
        classes = list(model.classes_)
        idx = classes.index(classe_predite)
        probabilite = round(float(proba[idx]) * 100, 1)
        # Score de risque global = probabilité pondérée vers le risque élevé/modéré
        poids = {"FAIBLE": 0.0, "MODERE": 0.5, "ELEVE": 1.0}
        score_risque = round(
            sum(proba[classes.index(c)] * poids.get(c, 0.5) for c in classes) * 100, 1
        )

    facteurs = _facteurs_principaux(model, features, data)

    return {
        "niveau_risque": classe_predite,
        "probabilite": probabilite if probabilite is not None else 0.0,
        "score_risque": score_risque if score_risque is not None else 0.0,
        "facteurs_principaux": facteurs,
        "recommandation": "\n".join(RECOMMANDATIONS.get(classe_predite, [])),
        "mention": MENTION_INDICATIVE,
    }


def _facteurs_principaux(model, features, data, top_n=5):
    """
    Identifie les facteurs les plus déterminants pour CET étudiant, en
    combinant l'importance globale du modèle (feature_importances_) et le
    caractère défavorable de la valeur déclarée par l'étudiant.
    """
    if not hasattr(model, "feature_importances_"):
        return []

    importances = model.feature_importances_
    scores = []
    for feat, imp in zip(features, importances):
        valeur = data.get(feat, 0)
        defavorable = _est_defavorable(feat, valeur)
        if defavorable:
            scores.append((feat, imp))

    scores.sort(key=lambda x: -x[1])
    return [LIBELLES_FACTEURS.get(feat, feat) for feat, _ in scores[:top_n]]


def _est_defavorable(feat, valeur):
    """Heuristique simple pour juger si une valeur déclarée est défavorable."""
    try:
        valeur = float(valeur)
    except (TypeError, ValueError):
        return False

    if feat in {"stress", "fatigue", "charge_mentale", "sentiment_debordement"}:
        return valeur >= 4
    if feat in {"sommeil", "motivation", "concentration", "equilibre_vie_etudes"}:
        return valeur <= 2
    if feat in {"heures_sommeil_jour"}:
        return valeur < 6
    if feat in {"temps_repos_jour"}:
        return valeur < 1.5
    if feat in {"heures_etude_jour"}:
        return valeur >= 6
    if feat in {"heures_cours_semaine"}:
        return valeur >= 25
    if feat in {"nombre_devoirs", "nombre_projets", "nombre_examens", "nombre_echeances_semaine"}:
        return valeur >= 5
    return False
