-- ============================================================
-- Contrôle 1 : Rapprochement volumétrique source/intégré/diffusé
-- Objectif : détecter les flux avec perte de lignes entre étapes
-- ============================================================
SELECT
    flux_nom,
    MAX(CASE WHEN etape = 'source' THEN nb_lignes END)   AS nb_source,
    MAX(CASE WHEN etape = 'integre' THEN nb_lignes END)  AS nb_integre,
    MAX(CASE WHEN etape = 'diffuse' THEN nb_lignes END)  AS nb_diffuse,
    MAX(CASE WHEN etape = 'source' THEN nb_lignes END)
        - MAX(CASE WHEN etape = 'diffuse' THEN nb_lignes END) AS ecart_total
FROM flux_log
GROUP BY flux_nom
HAVING ecart_total <> 0;

-- ============================================================
-- Contrôle 2 : Employés actifs sans identité SI (orphelins)
-- Objectif : détecter les incohérences référentiel RH -> IAM
-- ============================================================
SELECT e.matricule, e.nom, e.prenom, e.statut
FROM employees e
LEFT JOIN identities i ON e.matricule = i.matricule
WHERE i.identifiant_si IS NULL
  AND e.statut = 'actif';

-- ============================================================
-- Contrôle 3 : Doublons de droits d'accès
-- Objectif : même identité + même application + même rôle attribué plusieurs fois
-- ============================================================
SELECT identifiant_si, application, role, COUNT(*) AS nb_occurrences
FROM access_rights
GROUP BY identifiant_si, application, role
HAVING COUNT(*) > 1;

-- ============================================================
-- Contrôle 4 : Identités sans aucun droit d'accès
-- Objectif : détecter les comptes SI orphelins côté droits
-- ============================================================
SELECT i.identifiant_si, i.matricule, i.source_systeme
FROM identities i
LEFT JOIN access_rights ar ON i.identifiant_si = ar.identifiant_si
WHERE ar.id IS NULL;