import os
import sys
import requests

XRAY_CLIENT_ID = os.environ["XRAY_CLIENT_ID"]
XRAY_CLIENT_SECRET = os.environ["XRAY_CLIENT_SECRET"]

AUTH_URL = "https://us.xray.cloud.getxray.app/api/v2/authenticate"
IMPORT_URL = "https://us.xray.cloud.getxray.app/api/v2/import/execution/junit"

# Chaque rapport pousse vers SA propre Test Execution
REPORTS = [
    {
        "path": os.environ.get("JUNIT_REPORT_PATH", "report.xml"),
        "label": "pytest",
        "test_exec_key": os.environ.get("XRAY_TEST_EXECUTION_KEY_PYTEST", "SEMA-6"),
    },
    {
        "path": os.environ.get("NEWMAN_REPORT_PATH", "newman-report.xml"),
        "label": "newman",
        "test_exec_key": os.environ.get("XRAY_TEST_EXECUTION_KEY_NEWMAN"),  # pas de défaut : doit être fourni
    },
]


def authenticate():
    resp = requests.post(AUTH_URL, json={
        "client_id": XRAY_CLIENT_ID,
        "client_secret": XRAY_CLIENT_SECRET
    })
    resp.raise_for_status()
    token = resp.json()
    return token.strip('"')


def push_report(token, path, label, test_exec_key):
    if not test_exec_key:
        print(f"[{label}] Pas de testExecKey configuré — ignoré (Jira pas encore créé ?).")
        return None

    if not os.path.exists(path):
        print(f"[{label}] Fichier {path} introuvable — ignoré.")
        return None

    with open(path, "rb") as f:
        xml_content = f.read()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/xml"
    }
    params = {"testExecKey": test_exec_key}

    resp = requests.post(IMPORT_URL, headers=headers, params=params, data=xml_content)

    if resp.status_code not in (200, 201):
        print(f"[{label}] Erreur lors de l'envoi vers Xray : {resp.status_code}")
        print(resp.text)
        return False

    print(f"[{label}] Résultats envoyés avec succès vers Xray ({test_exec_key}).")
    print(resp.json())
    return True


if __name__ == "__main__":
    token = authenticate()

    results = []
    for report in REPORTS:
        outcome = push_report(token, report["path"], report["label"], report["test_exec_key"])
        results.append(outcome)

    if all(r is None for r in results):
        print("Aucun rapport n'a été envoyé (aucune clé configurée ou aucun fichier trouvé).")
        sys.exit(1)

    if any(r is False for r in results):
        sys.exit(1)

    sys.exit(0)
