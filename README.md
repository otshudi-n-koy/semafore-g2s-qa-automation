# SEMAFORE G2S — QA Automation Demo

Environnement de démonstration technique préparé en réponse à l'offre **G2S — Testeur fonctionnel SEMAFORE** (recette de données, flux, batch, API, sur un concentrateur de données interconnecté à un référentiel RH/IAM).

> ⚠️ Ce dépôt est un environnement de démonstration : mock applicatif et données synthétiques, construit pour illustrer une méthodologie de recette (contrôles de cohérence, industrialisation des tests, gestion Xray) transposable au périmètre réel SEMAFORE.

## Contexte

L'offre demande de sécuriser la qualité des livraisons SEMAFORE via : stratégie de recette documentée, contrôles de données (SQL/Power Query), tests automatisés (API, non-régression), et un patrimoine de tests structuré dans Xray pour Jira Cloud. Ce dépôt illustre chacun de ces points sur un jeu de données reconstitué.

## Contenu du dépôt

| Dossier | Contenu |
|---|---|
| `app/` | Mock API FastAPI simulant le concentrateur de données (employés, identités, droits d'accès, statut des flux) |
| `db/` | Modèle SQLAlchemy + génération de données synthétiques avec anomalies volontaires (seed idempotent) |
| `sql/` | Scripts SQL de contrôle (rapprochement volumétrique, doublons, cohérence référentielle) |
| `tests/` | Tests pytest de non-régression sur les mêmes règles de gestion |
| `postman/` | Collection Postman/Newman (6 tests API, mappés 1:1 aux Tests Xray `SEMA-11` à `SEMA-16`) |
| `powerquery/` | Classeur Excel avec requêtes Power Query reproduisant les contrôles SQL |
| `.github/workflows/` | Pipeline CI/CD GitHub Actions (seed → contrôles SQL → pytest → API → Newman → Xray) |
| `docs/` | Document de stratégie de recette (structuré sur la trame de livrables de l'offre) |
| `scripts/` | Synchronisation des résultats vers Xray Cloud (`push_to_xray.py`) et enrichissement du rapport JUnit Newman (`enrich_newman_report.py`) |

## Anomalies volontaires dans le jeu de données

Pour valider que les contrôles détectent réellement des écarts (et pas seulement qu'ils s'exécutent sans erreur), le jeu de données injecte :
- des employés actifs sans identité SI (orphelins référentiels)
- des doublons de droits d'accès (même application/role attribués deux fois à une même identité)
- des écarts de volumétrie entre les étapes source / intégré / diffusé d'un flux

Ces anomalies sont détectées de façon cohérente par les 4 canaux de contrôle : SQL, Power Query, pytest, et l'API (via Postman/Newman).

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

Un fichier d'environnement Postman (`SEMAFORE_Local.postman_environment.json`, non versionné) peut être importé dans l'app Postman pour l'usage manuel en local — il définit `base_url = http://localhost:8000`.

## Génération du jeu de données de démonstration

Le script `db/seed.py` est le point d'entrée pour alimenter la base SQLite de démonstration. Il crée intentionnellement un dataset synthétique construit pour reproduire les écarts métier que la recette doit détecter :

- 100 employés, dont seulement 95 identités SI (anomalie volontaire de référence)
- plusieurs droits d'accès par identité, dont des doublons explicites sur une même application/role (identité `SI_MAT0001`)
- 3 flux de traitement avec écarts de volumétrie entre l'étape source, intégration et diffusion

Le script est **idempotent** : un guard vérifie si la base contient déjà des employés avant de rejouer l'insertion, pour éviter les violations de contrainte `UNIQUE` (`matricule`) sur les redémarrages successifs d'un même environnement Docker.

Ces anomalies sont volontairement présentes pour vérifier que les contrôles SQL, les requêtes Power Query, les tests pytest et les tests API remontent bien des écarts de qualité et non pas un jeu de données parfait.

## Démarrage via Docker

Pour lancer l'environnement sans installer Python/conda en local :

```bash
docker compose up --build
```

Cela génère automatiquement les données (service `seed`, idempotent) puis démarre l'API sur `http://localhost:8000/docs`. Les données sont persistées dans un volume Docker (`dbdata`) entre les redémarrages.

Pour repartir d'un environnement totalement propre (reset complet des données) :

```bash
docker compose down -v
docker compose up --build
```

Pour arrêter sans supprimer les données :

```bash
docker compose down
```

## Endpoints API disponibles

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/` | Healthcheck |
| `GET` | `/employees` | Liste des employés, filtre optionnel `?statut=` |
| `GET` | `/employees/{matricule}` | Détail d'un employé, `404` si inexistant |
| `GET` | `/identities` | Liste des identités SI |
| `GET` | `/access-rights/{identifiant_si}` | Droits d'accès d'une identité |
| `GET` | `/flux/status` | Statut des étapes de chaque flux (source/intégré/diffusé) |

## Gestion des tests — Xray / Jira Cloud

Un projet Jira Cloud dédié (clé `SEMA`) structure le patrimoine de tests, réparti en **deux Test Executions distinctes** correspondant aux deux canaux d'automatisation :

| Test Execution | Canal | Tests couverts |
|---|---|---|
| `SEMA-6` | pytest (contrôles SQL / règles de gestion) | Tests de non-régression sur les anomalies de données |
| `SEMA-17` | Postman/Newman (API) | `SEMA-11` à `SEMA-16` — healthcheck, liste employés, filtre statut, 404, doublon droits d'accès, anomalies de flux |

Chaque Test Xray est de type **Generic** (requis pour l'import automatisé JUnit — un Test de type Manual ne peut pas recevoir de résultat automatisé).

### Le mécanisme de rattachement `test_key`

Xray Cloud n'associe **pas** un résultat JUnit à un Test existant par correspondance de nom ou de Summary : sans indication explicite, chaque import crée un nouveau Test générique, ce qui pollue rapidement le projet Jira. Le seul mécanisme fiable est l'injection d'une propriété dédiée dans chaque `<testcase>` du XML :

```xml
<testcase name="..." classname="...">
  <properties>
    <property name="test_key" value="SEMA-11"/>
  </properties>
</testcase>
```

Le reporter JUnit natif de Newman ne génère pas ce bloc — il faut donc **post-traiter** le rapport avant l'envoi à Xray. C'est le rôle de `scripts/enrich_newman_report.py` :

```bash
python scripts/enrich_newman_report.py newman-report.xml newman-report-xray.xml
```

Le script s'appuie sur un mapping interne `classname → clé Xray` (dérivé du nom des requêtes Postman) pour injecter la bonne propriété sur chacun des 6 testcases avant l'import.

### Synchronisation automatique CI → Xray

Le pipeline CI/CD pousse automatiquement les résultats vers Xray à chaque exécution, via `scripts/push_to_xray.py` :
- Push distinct pour pytest (`report.xml` → `SEMA-6`) et pour Newman (`newman-report-xray.xml` enrichi → `SEMA-17`), via deux variables d'environnement (`XRAY_TEST_EXECUTION_KEY_PYTEST`, `XRAY_TEST_EXECUTION_KEY_NEWMAN`)
- Si `XRAY_TEST_EXECUTION_KEY_NEWMAN` n'est pas configurée, ce push est ignoré proprement (log explicite) sans faire échouer le pipeline
- Les étapes API / Newman / enrichissement / push Xray s'exécutent **même si pytest échoue** (`if: always()`), pour que les statuts FAILED remontent aussi dans Xray
- Authentification via Client ID / Client Secret Xray Cloud, stockés en secrets GitHub (`XRAY_CLIENT_ID`, `XRAY_CLIENT_SECRET`) — jamais en clair dans le dépôt

Pour rejouer la synchronisation complète en local :

```bash
export XRAY_CLIENT_ID="..."
export XRAY_CLIENT_SECRET="..."
export XRAY_TEST_EXECUTION_KEY_PYTEST="SEMA-6"
export XRAY_TEST_EXECUTION_KEY_NEWMAN="SEMA-17"

pytest tests/ -v --junitxml=report.xml
newman run postman/semafore-api-tests.postman_collection.json --env-var base_url=http://127.0.0.1:8000 --reporters "cli,junit" --reporter-junit-export newman-report.xml
python scripts/enrich_newman_report.py newman-report.xml newman-report-xray.xml
NEWMAN_REPORT_PATH=newman-report-xray.xml python scripts/push_to_xray.py
```

## Pipeline CI/CD

Séquence complète du workflow GitHub Actions :

1. Checkout + setup Python
2. Génération des données mock (seed idempotent)
3. Contrôles SQL
4. Tests pytest (avec export JUnit)
5. Démarrage de l'API en arrière-plan (healthcheck en boucle avant de continuer)
6. Setup Node.js + installation de Newman
7. Exécution de la collection Postman (avec export JUnit)
8. Enrichissement du rapport Newman (injection des `test_key` Xray)
9. Push des deux rapports (pytest + Newman enrichi) vers leurs Test Executions Xray respectives

Le pipeline échoue volontairement à l'étape des tests pytest tant que les anomalies de données ne sont pas résolues — comportement assumé, simulant un contrôle qualité bloquant avant livraison. Grâce aux `if: always()` sur les étapes suivantes, les résultats (succès et échecs, pytest comme Newman) sont malgré tout systématiquement remontés vers Xray.

## Stratégie de recette

Voir [`docs/Strategie_Recette_SEMAFORE.docx`](docs/Strategie_Recette_SEMAFORE.docx) : document structuré sur les 9 points de livrables attendus par l'offre (état des lieux, stratégie, plans de test, patrimoine Xray, rapports, scripts versionnés, procédures, tableaux de bord, transfert de compétences).

## Stack technique

Python 3.11 · FastAPI · SQLAlchemy · SQLite · pytest · Postman/Newman · GitHub Actions · Power Query (Excel) · Jira Cloud / Xray · Docker

---

**Auteur** : N'Koy Otshudi — Consultant QA Automation Senior / Test Lead
[linkedin.com/in/otshudi-n-koy](https://linkedin.com/in/otshudi-n-koy) · [github.com/otshudi-n-koy](https://github.com/otshudi-n-koy)
