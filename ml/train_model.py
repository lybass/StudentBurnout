"""
Entraîne le modèle de classification du niveau de risque de burnout étudiant.

Usage :
    python ml/train_model.py

Ce script :
1. charge ml/dataset.csv (dataset synthétique de démonstration) ;
2. nettoie/vérifie les données ;
3. sépare features (X) et cible (y) ;
4. divise en train/test ;
5. entraîne un RandomForestClassifier ;
6. calcule accuracy / precision / recall / F1-score ;
7. affiche la matrice de confusion ;
8. sauvegarde le modèle entraîné avec joblib dans ml/burnout_model.pkl.

Les métriques affichées sont celles réellement obtenues sur le jeu de test,
sans arrangement artificiel.
"""
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

# Ordre des variables utilisé PARTOUT (entraînement + prédiction en production).
# burnout/ml_model.py doit respecter exactement cet ordre.
FEATURES = [
    "stress", "fatigue", "motivation", "concentration", "sommeil",
    "charge_mentale", "sentiment_debordement", "equilibre_vie_etudes",
    "heures_cours_semaine", "heures_etude_jour", "heures_sommeil_jour",
    "nombre_devoirs", "nombre_projets", "nombre_examens",
    "nombre_echeances_semaine", "temps_repos_jour",
]
TARGET = "niveau_risque"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "ml", "dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "burnout_model.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "ml", "metrics.json")


def main():
    print(f"Chargement du dataset : {DATASET_PATH}")
    df = pd.read_csv(DATASET_PATH)

    # Vérification et nettoyage minimal
    missing_cols = [c for c in FEATURES + [TARGET] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Colonnes manquantes dans le dataset : {missing_cols}")

    before = len(df)
    df = df.dropna(subset=FEATURES + [TARGET])
    dropped = before - len(df)
    if dropped:
        print(f"{dropped} lignes avec valeurs manquantes ont été supprimées.")

    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=3,
        random_state=42,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, average="macro", zero_division=0)
    recall = recall_score(y_test, y_pred, average="macro", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="macro", zero_division=0)

    labels = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)

    print("\n===== RÉSULTATS RÉELS SUR LE JEU DE TEST =====")
    print(f"Accuracy  : {accuracy:.3f}")
    print(f"Precision (macro) : {precision:.3f}")
    print(f"Recall (macro)    : {recall:.3f}")
    print(f"F1-score (macro)  : {f1:.3f}")
    print("\nMatrice de confusion (lignes = vrai, colonnes = prédit) :")
    print(f"Classes : {labels}")
    print(cm)
    print("\nRapport détaillé :")
    print(classification_report(y_test, y_pred, zero_division=0))

    importances = dict(zip(FEATURES, model.feature_importances_.tolist()))
    print("Importance des variables :")
    for feat, imp in sorted(importances.items(), key=lambda x: -x[1]):
        print(f"  {feat:30s} {imp:.3f}")

    # Sauvegarde du modèle + métadonnées nécessaires à la prédiction
    payload = {
        "model": model,
        "features": FEATURES,
        "classes": model.classes_.tolist(),
    }
    joblib.dump(payload, MODEL_PATH)
    print(f"\nModèle sauvegardé : {MODEL_PATH}")

    metrics = {
        "accuracy": accuracy,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
        "confusion_matrix": cm.tolist(),
        "labels": labels,
        "feature_importances": importances,
        "n_train": len(X_train),
        "n_test": len(X_test),
    }
    with open(METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"Métriques sauvegardées : {METRICS_PATH}")


if __name__ == "__main__":
    main()
