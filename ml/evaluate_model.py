"""
Évalue indépendamment le modèle sauvegardé (ml/burnout_model.pkl) sur le
dataset complet, en ré-appliquant un split train/test identique à celui de
l'entraînement (random_state=42) afin de vérifier les métriques annoncées.

Usage :
    python ml/evaluate_model.py
"""
import os

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_PATH = os.path.join(BASE_DIR, "ml", "dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "ml", "burnout_model.pkl")


def main():
    if not os.path.exists(MODEL_PATH):
        print(f"Modèle introuvable : {MODEL_PATH}. Lancez d'abord train_model.py.")
        return

    payload = joblib.load(MODEL_PATH)
    model = payload["model"]
    features = payload["features"]

    df = pd.read_csv(DATASET_PATH).dropna(subset=features + ["niveau_risque"])
    X = df[features]
    y = df["niveau_risque"]

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    y_pred = model.predict(X_test)

    print(f"Accuracy sur le jeu de test : {accuracy_score(y_test, y_pred):.3f}")
    print("\nRapport détaillé :")
    print(classification_report(y_test, y_pred, zero_division=0))
    print("Matrice de confusion :")
    print(confusion_matrix(y_test, y_pred, labels=sorted(y.unique())))


if __name__ == "__main__":
    main()
