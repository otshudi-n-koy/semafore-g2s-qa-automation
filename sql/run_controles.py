import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "semafore.db")
SQL_PATH = os.path.join(os.path.dirname(__file__), "controles_rapprochement.sql")

with open(SQL_PATH, "r", encoding="utf-8") as f:
    sql_content = f.read()

raw_blocks = [b.strip() for b in sql_content.split(";") if b.strip()]

queries = []
for block in raw_blocks:
    # enlève les lignes de commentaire, garde uniquement le SQL
    lines = [l for l in block.splitlines() if not l.strip().startswith("--")]
    cleaned = "\n".join(lines).strip()
    if cleaned:
        queries.append(cleaned)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

titles = [
    "CONTROLE 1 - Ecarts de volumetrie source/integre/diffuse",
    "CONTROLE 2 - Employes actifs sans identite SI",
    "CONTROLE 3 - Doublons de droits d'acces",
    "CONTROLE 4 - Identites sans droit d'acces",
]

print(f"Nombre de requetes detectees : {len(queries)}")

for i, query in enumerate(queries):
    title = titles[i] if i < len(titles) else f"REQUETE {i+1}"
    print(f"\n{'='*60}\n{title}\n{'='*60}")
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    print(" | ".join(columns))
    if not rows:
        print("(aucun résultat)")
    for row in rows:
        print(" | ".join(str(v) for v in row))

conn.close()