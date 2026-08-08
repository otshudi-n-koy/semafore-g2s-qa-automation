# SEMAFORE G2S — QA Automation Demo

Environnement de démonstration technique préparé en réponse à l'offre **G2S — Testeur fonctionnel SEMAFORE** (recette de données, flux, batch, API, sur un concentrateur de données interconnecté à un référentiel RH/IAM).

> ⚠️ Ce dépôt est un environnement de démonstration : mock applicatif et données synthétiques, construit pour illustrer une méthodologie de recette (contrôles de cohérence, industrialisation des tests, gestion Xray) transposable au périmètre réel SEMAFORE.

## Contexte

L'offre demande de sécuriser la qualité des livraisons SEMAFORE via : stratégie de recette documentée, contrôles de données (SQL/Power Query), tests automatisés (API, non-régression), et un patrimoine de tests structuré dans Xray pour Jira Cloud. Ce dépôt illustre chacun de ces points sur un jeu de données reconstitué.

## Contenu du dépôt

| Dossier | Contenu |
|---|---|
| `app/` | Mock API FastAPI simulant le concentrateur de données (employés, identités, droits d'accès, statut des flux) |
| `db/` | Modèle SQLAlchemy + génération de données synthétiques avec anomalies volontaires |
| `sql/` | Scripts SQL de contrôle (rapprochement volumétrique, doublons, cohérence référentielle) |
| `tests/` | Tests pytest de non-régression sur les mêmes règles de gestion |
| `postman/` | Collection Postman/Newman (10 tests API) |
| `powerquery/` | Classeur Excel avec requêtes Power Query reproduisant les contrôles SQL |
| `.github/workflows/` | Pipeline CI/CD GitHub Actions (seed → contrôles SQL → pytest → API → Newman) |
| `docs/` | Document de stratégie de recette (structuré sur la trame de livrables de l'offre) |

## Anomalies volontaires dans le jeu de données

Pour valider que les contrôles détectent réellement des écarts (et pas seulement qu'ils s'exécutent sans erreur), le jeu de données injecte :
- des employés actifs sans identité SI (orphelins référentiels)
- des doublons de droits d'accès
- des écarts de volumétrie entre les étapes source / intégré / diffusé d'un flux

Ces anomalies sont détectées de façon cohérente par les 3 canaux de contrôle : SQL, Power Query, et pytest.

## Démarrage rapide

```bash
conda create -n semafore-qa python=3.11 -y
conda activate semafore-qa
pip install -r requirements.txt

# Générer les données (avec anomalies volontaires)
python -m db.seed

# Lancer les contrôles SQL
python sql/run_controles.py

# Lancer les tests de non-régression
pytest tests/ -v

# Démarrer l'API mock
python -m uvicorn app.main:app --reload
# Swagger : http://127.0.0.1:8000/docs
```

Pour rejouer la collection Postman en CLI (Newman) :

```bash
npm install -g newman
newman run postman/semafore-api-tests.postman_collection.json --env-var base_url=http://127.0.0.1:8000
```

## Gestion des tests — Xray / Jira Cloud

Un projet Jira Cloud dédié (clé `SEMA`) structure le patrimoine de tests :
- 4 cas de test (Manual, Action/Données/Résultat attendu)
- 1 Test Plan regroupant les 4 cas
- 1 Test Execution avec statut d'exécution global et historique

Chaque cas de test est lié au script SQL correspondant dans ce dépôt.

## Pipeline CI/CD

Le pipeline GitHub Actions échoue volontairement à l'étape des tests pytest tant que les anomalies de données ne sont pas résolues — comportement assumé, simulant un contrôle qualité bloquant avant livraison.

## Stratégie de recette

Voir [`docs/Strategie_Recette_SEMAFORE.docx`](docs/Strategie_Recette_SEMAFORE.docx) : document structuré sur les 9 points de livrables attendus par l'offre (état des lieux, stratégie, plans de test, patrimoine Xray, rapports, scripts versionnés, procédures, tableaux de bord, transfert de compétences).

## Stack technique

Python 3.11 · FastAPI · SQLAlchemy · SQLite · pytest · Postman/Newman · GitHub Actions · Power Query (Excel) · Jira Cloud / Xray

---

**Auteur** : N'Koy Otshudi — Consultant QA Automation Senior / Test Lead
[linkedin.com/in/otshudi-n-koy](https://linkedin.com/in/otshudi-n-koy) · [github.com/otshudi-n-koy](https://github.com/otshudi-n-koy)