# StudentBurnout

**Plateforme intelligente de détection et de prévention du risque de burnout étudiant.**

Projet académique de Master (programme MILIA — Ingénierie Logicielle et Intelligence
Artificielle, École Polytechnique de Thiès).

> ⚠️ Cet outil fournit une **estimation indicative** et ne remplace en aucun cas l'avis
> d'un professionnel de santé. Il ne pose pas de diagnostic médical.

## Description

StudentBurnout permet à un étudiant de :
1. créer un profil ;
2. remplir un questionnaire sur son état général et sa charge académique ;
3. renseigner sa charge de travail (heures de cours, d'étude, de sommeil, devoirs, projets, examens) ;
4. obtenir, via un modèle de Machine Learning, une **estimation** de son niveau de risque
   (FAIBLE / MODÉRÉ / ÉLEVÉ) ;
5. consulter les principaux indicateurs associés à cette estimation ;
6. recevoir des recommandations générales et prudentes ;
7. suivre l'évolution de ses résultats dans le temps via un tableau de bord et un historique.

## Objectifs

- Illustrer un pipeline Machine Learning complet (données → entraînement → évaluation →
  intégration en production) dans une application Django réelle.
- Sensibiliser à la charge académique et à ses indicateurs, sans jamais prétendre à un
  diagnostic médical.

## Fonctionnalités

- Authentification (inscription, connexion, déconnexion, gestion du profil).
- Questionnaire structuré en 4 sections (état général, sommeil, études, équilibre).
- Suivi périodique de la charge de travail avec statistiques (moyennes, historique).
- Prédiction du niveau de risque par un modèle `RandomForestClassifier` (scikit-learn).
- Affichage des facteurs principaux associés à l'estimation (basés sur
  `feature_importances_` du modèle et les valeurs déclarées par l'étudiant).
- Recommandations différenciées selon le niveau de risque.
- Tableau de bord avec graphiques (Chart.js) : évolution du score de risque, du temps
  d'étude, de sommeil et de repos.
- Historique complet des évaluations, avec accès restreint aux données du propriétaire.
- Interface d'administration Django pour la gestion des étudiants, questionnaires,
  charges de travail et résultats.

## Technologies

- **Backend** : Python 3, Django (ORM, Auth, Admin)
- **Base de données** : SQLite
- **Frontend** : Templates Django, HTML5, CSS3, Bootstrap 5, JavaScript
- **Machine Learning** : pandas, numpy, scikit-learn, joblib
- **Visualisation** : Chart.js

## Architecture

```
StudentBurnout/
│
├── manage.py
├── requirements.txt
├── README.md
│
├── StudentBurnout/              # Configuration du projet Django
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── burnout/                     # Application principale
│   ├── migrations/
│   ├── templates/burnout/       # Templates HTML (Bootstrap 5)
│   ├── static/burnout/          # CSS / JS
│   ├── models.py                # Etudiant, Questionnaire, ChargeTravail, Resultat
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── ml_model.py              # Intégration du modèle ML dans Django
│   └── tests.py
│
└── ml/                           # Pipeline Machine Learning
    ├── generate_dataset.py       # Génère le dataset synthétique
    ├── dataset.csv               # Dataset de démonstration (synthétique)
    ├── train_model.py            # Entraînement + évaluation + sauvegarde du modèle
    ├── evaluate_model.py         # Évaluation indépendante du modèle sauvegardé
    ├── burnout_model.pkl         # Modèle entraîné (généré)
    └── metrics.json              # Métriques réelles du dernier entraînement
```

## Installation

```bash
python -m venv venv
```

Activation de l'environnement virtuel :

- **Linux / macOS** : `source venv/bin/activate`
- **Windows** : `venv\Scripts\activate`

Installation des dépendances :

```bash
pip install -r requirements.txt
```

Migrations de la base de données :

```bash
python manage.py makemigrations
python manage.py migrate
```

Création d'un compte administrateur :

```bash
python manage.py createsuperuser
```

## Machine Learning

Le dataset fourni (`ml/dataset.csv`) est **synthétique** : il est généré par
`ml/generate_dataset.py` à partir de règles statistiques et de bruit aléatoire, à des
fins pédagogiques uniquement. Il ne provient d'aucune étude réelle et ne représente pas
scientifiquement la population étudiante.

Pour régénérer le dataset :

```bash
python ml/generate_dataset.py
```

Pour entraîner (ou ré-entraîner) le modèle :

```bash
python ml/train_model.py
```

Le script affiche les métriques **réellement obtenues** sur le jeu de test (accuracy,
precision, recall, F1-score, matrice de confusion) — aucune performance n'est fabriquée
artificiellement. Le modèle est sauvegardé dans `ml/burnout_model.pkl` et chargé
automatiquement par `burnout/ml_model.py` lors des prédictions.

Pour évaluer le modèle sauvegardé indépendamment :

```bash
python ml/evaluate_model.py
```

## Lancement de l'application

```bash
python manage.py runserver
```

L'application est accessible à l'adresse : http://127.0.0.1:8000/

## Tests

```bash
python manage.py test
```

Les tests couvrent : inscription, connexion, protection des pages privées, validation
du questionnaire, parcours complet jusqu'au résultat, et l'impossibilité pour un
étudiant de consulter le résultat d'un autre étudiant.

## Sécurité

- Protection CSRF activée sur tous les formulaires.
- Pages privées protégées par `@login_required`.
- Chaque étudiant ne peut consulter que ses propres données (vérification systématique
  de la propriété des objets dans les vues, réponse `404` sinon).
- `SECRET_KEY`, `DEBUG` et `ALLOWED_HOSTS` configurables via variables d'environnement
  (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`) pour la mise en production.
- Aucune traceback Python n'est affichée à l'utilisateur final (messages Django utilisés
  pour les erreurs : `messages.success/error/warning`).

## Limites

- Le dataset d'entraînement est synthétique ; les performances du modèle (~49 %
  d'accuracy sur 3 classes) reflètent la difficulté du problème sur des données
  simulées et ne doivent pas être interprétées comme une performance clinique.
- L'application ne pose aucun diagnostic médical : elle fournit uniquement une
  estimation indicative destinée à sensibiliser l'étudiant à sa charge académique.
- Les recommandations sont volontairement générales et prudentes.

## Perspectives

- Remplacer le dataset synthétique par des données réelles et anonymisées (avec accord
  éthique approprié).
- Ajouter un module de notifications/rappels pour le suivi régulier de la charge de travail.
- Explorer d'autres modèles (gradient boosting, réseaux de neurones) et une validation
  croisée plus poussée.
- Ajouter une API REST pour une éventuelle application mobile.
