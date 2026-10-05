"""
Génère un dataset SYNTHÉTIQUE pédagogique pour l'entraînement du modèle
StudentBurnout.

⚠️ Ces données sont artificielles et générées par règles + bruit aléatoire.
Elles ne proviennent d'aucune étude réelle et NE représentent PAS
scientifiquement la population étudiante. Elles servent uniquement à
illustrer un pipeline de Machine Learning complet dans un cadre académique.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)
N = 1200


def clip_scale(x):
    return np.clip(np.round(x), 1, 5).astype(int)


def generate():
    # Variables latentes de base (0 à 1) représentant un "profil de charge"
    profil = RNG.beta(2, 2, N)  # 0 = étudiant serein, 1 = étudiant très sollicité

    stress = clip_scale(1 + 4 * profil + RNG.normal(0, 0.7, N))
    fatigue = clip_scale(1 + 4 * profil + RNG.normal(0, 0.7, N))
    motivation = clip_scale(5 - 3 * profil + RNG.normal(0, 0.8, N))
    concentration = clip_scale(5 - 3.5 * profil + RNG.normal(0, 0.8, N))
    sentiment_debordement = clip_scale(1 + 4 * profil + RNG.normal(0, 0.6, N))
    sommeil = clip_scale(5 - 3 * profil + RNG.normal(0, 0.8, N))
    charge_mentale = clip_scale(1 + 4 * profil + RNG.normal(0, 0.6, N))
    equilibre_vie_etudes = clip_scale(5 - 3.5 * profil + RNG.normal(0, 0.8, N))

    heures_cours_semaine = np.clip(10 + 15 * profil + RNG.normal(0, 3, N), 0, 40)
    heures_etude_jour = np.clip(1 + 5 * profil + RNG.normal(0, 1, N), 0, 12)
    heures_sommeil_jour = np.clip(8 - 3 * profil + RNG.normal(0, 0.8, N), 3, 10)
    nombre_devoirs = np.clip(np.round(1 + 6 * profil + RNG.normal(0, 1.5, N)), 0, 12).astype(int)
    nombre_projets = np.clip(np.round(4 * profil + RNG.normal(0, 1, N)), 0, 6).astype(int)
    nombre_examens = np.clip(np.round(3 * profil + RNG.normal(0, 1, N)), 0, 6).astype(int)
    temps_repos_jour = np.clip(4 - 3 * profil + RNG.normal(0, 0.8, N), 0, 6)

    # Score de risque latent combinant les indicateurs (pondération pédagogique)
    score = (
        0.18 * stress
        + 0.16 * fatigue
        + 0.14 * charge_mentale
        + 0.14 * sentiment_debordement
        + 0.12 * (6 - sommeil)
        + 0.10 * (6 - equilibre_vie_etudes)
        + 0.08 * (heures_etude_jour / 2.4)
        + 0.08 * (nombre_echeances := np.clip(np.round(nombre_devoirs / 2 + nombre_projets + nombre_examens
                                                         + RNG.normal(0, 1, N)), 0, 15).astype(int)) / 3
    )
    score = score + RNG.normal(0, 1.2, N)

    q1, q2 = np.quantile(score, [0.40, 0.75])
    niveau = np.where(score <= q1, "FAIBLE", np.where(score <= q2, "MODERE", "ELEVE"))

    df = pd.DataFrame({
        "stress": stress,
        "fatigue": fatigue,
        "motivation": motivation,
        "concentration": concentration,
        "sommeil": sommeil,
        "charge_mentale": charge_mentale,
        "sentiment_debordement": sentiment_debordement,
        "equilibre_vie_etudes": equilibre_vie_etudes,
        "heures_cours_semaine": np.round(heures_cours_semaine, 1),
        "heures_etude_jour": np.round(heures_etude_jour, 1),
        "heures_sommeil_jour": np.round(heures_sommeil_jour, 1),
        "nombre_devoirs": nombre_devoirs,
        "nombre_projets": nombre_projets,
        "nombre_examens": nombre_examens,
        "nombre_echeances_semaine": nombre_echeances,
        "temps_repos_jour": np.round(temps_repos_jour, 1),
        "niveau_risque": niveau,
    })
    return df


if __name__ == "__main__":
    df = generate()
    df.to_csv("ml/dataset.csv", index=False)
    print(f"Dataset synthétique généré : {len(df)} lignes -> ml/dataset.csv")
    print(df["niveau_risque"].value_counts())
