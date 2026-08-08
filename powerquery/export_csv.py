import sqlite3
import csv
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "semafore.db")
OUTPUT_DIR = os.path.dirname(__file__)

TABLES = ["employees", "identities", "access_rights", "flux_log"]

conn = sqlite3.connect(DB_PATH)

for table in TABLES:
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table}")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()

    csv_path = os.path.join(OUTPUT_DIR, f"{table}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"{table}.csv exporté ({len(rows)} lignes)")

conn.close()