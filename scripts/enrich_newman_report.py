"""
Post-traite le rapport JUnit généré par Newman pour y injecter la propriété
<properties><property name="test_key" value="SEMA-XX"/></properties>
dans chaque <testcase>, seul mécanisme fiable de rattachement Xray Cloud
(le nom du testcase ou le Summary Jira ne suffisent pas).

Usage :
    python scripts/enrich_newman_report.py newman-report.xml newman-report-xray.xml
"""
import sys
import xml.etree.ElementTree as ET

# Mapping : nom de la REQUETE Postman (attribut "classname" généré par Newman,
# dérivé du nom de la requête) -> clé Xray. A adapter si tu renommes des requêtes.
CLASSNAME_TO_TEST_KEY = {
    "Sema11GetRoot": "SEMA-11",
    "Sema12GetListEmployees": "SEMA-12",
    "Sema13GetEmployeesFilteredByStatut": "SEMA-13",
    "Sema14GetEmployeeNotFound": "SEMA-14",
    "Sema15GetAccessRightsDuplicateDetection": "SEMA-15",
    "Sema16GetFluxStatus": "SEMA-16",
}


def enrich(input_path, output_path):
    tree = ET.parse(input_path)
    root = tree.getroot()

    testcases = root.findall(".//testcase")
    if not testcases:
        print("Aucun <testcase> trouvé dans le rapport.")
        sys.exit(1)

    enriched_count = 0
    for tc in testcases:
        classname = tc.get("classname", "")
        test_key = CLASSNAME_TO_TEST_KEY.get(classname)

        if not test_key:
            print(f"[warn] Pas de mapping pour classname='{classname}' (testcase='{tc.get('name')}') — ignoré.")
            continue

        # Ne pas dupliquer si déjà présent
        existing_props = tc.find("properties")
        if existing_props is None:
            existing_props = ET.SubElement(tc, "properties")

        already_has_key = any(
            p.get("name") == "test_key" for p in existing_props.findall("property")
        )
        if not already_has_key:
            prop = ET.SubElement(existing_props, "property")
            prop.set("name", "test_key")
            prop.set("value", test_key)
            enriched_count += 1

    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"{enriched_count} testcase(s) enrichi(s) avec leur test_key Xray.")
    print(f"Rapport enrichi écrit dans : {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/enrich_newman_report.py <input.xml> <output.xml>")
        sys.exit(1)

    enrich(sys.argv[1], sys.argv[2])
