import sqlite3
import os
import pytest

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "semafore.db")


@pytest.fixture
def conn():
    connection = sqlite3.connect(DB_PATH)
    yield connection
    connection.close()


def test_SEMA_1_pas_de_perte_critique_sur_flux(conn, record_property):
    """
    Contrôle de non-régression : l'écart source->diffuse ne doit pas dépasser
    5% du volume source (seuil de tolérance métier à ajuster avec le client).
    """
    record_property("test_key", "SEMA-1")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            flux_nom,
            MAX(CASE WHEN etape = 'source' THEN nb_lignes END) AS nb_source,
            MAX(CASE WHEN etape = 'diffuse' THEN nb_lignes END) AS nb_diffuse
        FROM flux_log
        GROUP BY flux_nom
    """)
    rows = cursor.fetchall()
    assert rows, "Aucun flux trouvé en base"

    for flux_nom, nb_source, nb_diffuse in rows:
        ecart_pct = abs(nb_source - nb_diffuse) / nb_source * 100
        assert ecart_pct <= 5, (
            f"Flux {flux_nom} : écart de {ecart_pct:.1f}% entre source ({nb_source}) "
            f"et diffuse ({nb_diffuse}), dépasse le seuil de tolérance de 5%"
        )


def test_SEMA_2_aucun_employe_actif_sans_identite(conn, record_property):
    """
    Règle de gestion critique : tout employé actif doit avoir une identité SI
    (sinon perte d'accès aux applications RH/IAM).
    """

    record_property("test_key", "SEMA-2")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.matricule
        FROM employees e
        LEFT JOIN identities i ON e.matricule = i.matricule
        WHERE i.identifiant_si IS NULL AND e.statut = 'actif'
    """)
    orphelins = cursor.fetchall()
    assert not orphelins, (
        f"{len(orphelins)} employé(s) actif(s) sans identité SI : "
        f"{[m[0] for m in orphelins]}"
    )


def test_SEMA_3_pas_de_doublons_droits_acces(conn, record_property):
    """
    Contrôle qualité : un même droit (identité + appli + rôle) ne doit pas
    être attribué plusieurs fois (risque de sur-habilitation, audit sécurité).
    """
    record_property("test_key", "SEMA-3")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT identifiant_si, application, role, COUNT(*) as nb
        FROM access_rights
        GROUP BY identifiant_si, application, role
        HAVING nb > 1
    """)
    doublons = cursor.fetchall()
    assert not doublons, (
        f"{len(doublons)} doublon(s) de droits détecté(s) : {doublons}"
    )


def test_SEMA_4_toute_identite_a_au_moins_un_droit(conn, record_property):
    """
    Cohérence référentielle : une identité SI créée sans aucun droit d'accès
    est probablement un compte orphelin ou un défaut de provisioning.
    """
    record_property("test_key", "SEMA-4")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.identifiant_si
        FROM identities i
        LEFT JOIN access_rights ar ON i.identifiant_si = ar.identifiant_si
        WHERE ar.id IS NULL
    """)
    orphelins = cursor.fetchall()
    assert not orphelins, f"{len(orphelins)} identité(s) sans droit d'accès"