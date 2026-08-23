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
| `scripts/` | Script de synchronisation automatique des résultats pytest vers Xray Cloud (JUnit → API Xray) |

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

## Génération du jeu de données de démonstration

Le script `db/seed.py` est le point d'entrée pour alimenter la base SQLite de démonstration. Il crée intentionnellement un dataset synthétique construit pour reproduire les écarts métier que la recette doit détecter :

- 100 employés, dont seulement 95 identités SI (anomalie volontaire de référence)
- plusieurs droits d'accès par identité, dont des doublons explicites sur une même application/role
- 3 flux de traitement avec écarts de volumétrie entre l'étape source, intégration et diffusion

Ces anomalies sont volontairement présentes pour vérifier que les contrôles SQL, les requêtes Power Query et les tests pytest remontent bien des écarts de qualité et non pas un jeu de données parfait.

## Démarrage via Docker

Pour lancer l'environnement sans installer Python/conda en local :

```bash
docker compose up --build
```

Cela génère automatiquement les données (service `seed`) puis démarre l'API sur `http://localhost:8000/docs`. Les données sont persistées dans un volume Docker (`dbdata`) entre les redémarrages.

**Important** : si le volume `dbdata` existe déjà (run précédent), le service `seed` échoue car la base contient déjà des données. Pour repartir d'un environnement propre :

```bash
docker compose down -v
docker compose up --build
```

Pour arrêter sans supprimer les données :

```bash
docker compose down
```

## Gestion des tests — Xray / Jira Cloud

Un projet Jira Cloud dédié (clé `SEMA`) structure le patrimoine de tests :
- 4 cas de test (Manual, Action/Données/Résultat attendu)
- 1 Test Plan regroupant les 4 cas
- 1 Test Execution (`SEMA-6`) avec statut d'exécution global et historique

Chaque cas de test est lié au script SQL correspondant dans ce dépôt.

### Synchronisation automatique CI → Xray

Le pipeline CI/CD pousse automatiquement les résultats pytest vers la Test Execution Xray à chaque exécution, via `scripts/push_to_xray.py` :
- Chaque test pytest est mappé à sa clé Xray via `record_property("test_key", "SEMA-N")` (voir `tests/test_controles_donnees.py`)
- Le format JUnit `legacy` est requis pour que Xray reconnaisse la propriété (`pytest.ini`)
- L'étape d'envoi s'exécute **même si les tests échouent** (`if: always()`), pour que les statuts FAILED remontent aussi dans Xray
- Authentification via Client ID / Client Secret Xray Cloud, stockés en secrets GitHub (`XRAY_CLIENT_ID`, `XRAY_CLIENT_SECRET`) — jamais en clair dans le dépôt

Pour rejouer la synchronisation en local :

```bash
export XRAY_CLIENT_ID="..."
export XRAY_CLIENT_SECRET="..."
pytest tests/ -v --junitxml=report.xml
python scripts/push_to_xray.py
```

## Pipeline CI/CD

Le pipeline GitHub Actions échoue volontairement à l'étape des tests pytest tant que les anomalies de données ne sont pas résolues — comportement assumé, simulant un contrôle qualité bloquant avant livraison. Les résultats (succès et échecs) sont ensuite automatiquement remontés vers la Test Execution Xray, qu'ils échouent ou non.

## Stratégie de recette

Voir [`docs/Strategie_Recette_SEMAFORE.docx`](docs/Strategie_Recette_SEMAFORE.docx) : document structuré sur les 9 points de livrables attendus par l'offre (état des lieux, stratégie, plans de test, patrimoine Xray, rapports, scripts versionnés, procédures, tableaux de bord, transfert de compétences).

## Stack technique

Python 3.11 · FastAPI · SQLAlchemy · SQLite · pytest · Postman/Newman · GitHub Actions · Power Query (Excel) · Jira Cloud / Xray · Docker

---

**Auteur** : N'Koy Otshudi — Consultant QA Automation Senior / Test Lead
[linkedin.com/in/otshudi-n-koy](https://linkedin.com/in/otshudi-n-koy) · [github.com/otshudi-n-koy](https://github.com/otshudi-n-koy)