import os
import sys
import requests

XRAY_CLIENT_ID = os.environ["XRAY_CLIENT_ID"]
XRAY_CLIENT_SECRET = os.environ["XRAY_CLIENT_SECRET"]
TEST_EXECUTION_KEY = os.environ.get("XRAY_TEST_EXECUTION_KEY", "SEMA-6")
JUNIT_REPORT_PATH = os.environ.get("JUNIT_REPORT_PATH", "report.xml")

AUTH_URL = "https://us.xray.cloud.getxray.app/api/v2/authenticate"
IMPORT_URL = "https://us.xray.cloud.getxray.app/api/v2/import/execution/junit"


def authenticate():
    resp = requests.post(AUTH_URL, json={
        "client_id": XRAY_CLIENT_ID,
        "client_secret": XRAY_CLIENT_SECRET
    })
    resp.raise_for_status()
    token = resp.json()
    return token.strip('"')


def push_results(token):
    with open(JUNIT_REPORT_PATH, "rb") as f:
        xml_content = f.read()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/xml"
    }

    params = {"testExecKey": TEST_EXECUTION_KEY}

    resp = requests.post(IMPORT_URL, headers=headers, params=params, data=xml_content)

    if resp.status_code not in (200, 201):
        print(f"Erreur lors de l'envoi vers Xray : {resp.status_code}")
        print(resp.text)
        sys.exit(1)

    print("Résultats envoyés avec succès vers Xray.")
    print(resp.json())


if __name__ == "__main__":
    if not os.path.exists(JUNIT_REPORT_PATH):
        print(f"Fichier {JUNIT_REPORT_PATH} introuvable.")
        sys.exit(1)

    token = authenticate()
    push_results(token)