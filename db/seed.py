import random
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from db.models import init_db, Employee, Identity, AccessRight, FluxLog

engine = init_db()
Session = sessionmaker(bind=engine)
session = Session()

NOMS = ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Petit", "Durand", "Leroy", "Moreau", "Simon"]
PRENOMS = ["Jean", "Marie", "Pierre", "Sophie", "Luc", "Claire", "Paul", "Julie", "Marc", "Anne"]
APPS = ["SEMAFORE", "PORTAIL_RH", "ANNUAIRE_AD", "SI_PAIE"]
ROLES = ["lecture", "gestionnaire", "administrateur", "consultant"]

# 1. Employees (100 salariés)
employees = []
for i in range(1, 101):
    emp = Employee(
        matricule=f"MAT{i:04d}",
        nom=random.choice(NOMS),
        prenom=random.choice(PRENOMS),
        date_entree=datetime(2015, 1, 1) + timedelta(days=random.randint(0, 4000)),
        statut=random.choices(["actif", "sorti", "suspendu"], weights=[80, 15, 5])[0]
    )
    employees.append(emp)
session.add_all(employees)
session.commit()

# 2. Identities — on en crée volontairement MOINS que d'employés (5 manquants = anomalie)
identities = []
for emp in employees[:95]:
    ident = Identity(
        matricule=emp.matricule,
        identifiant_si=f"SI_{emp.matricule}",
        source_systeme=random.choice(["RH_SOURCE", "AD"]),
        date_creation=emp.date_entree + timedelta(days=random.randint(1, 10))
    )
    identities.append(ident)
session.add_all(identities)
session.commit()

# 3. Access rights (plusieurs par identité, avec quelques doublons volontaires)
access_rights = []
for ident in identities:
    nb_droits = random.randint(1, 3)
    for _ in range(nb_droits):
        ar = AccessRight(
            identifiant_si=ident.identifiant_si,
            application=random.choice(APPS),
            role=random.choice(ROLES),
            date_attribution=ident.date_creation + timedelta(days=random.randint(0, 100)),
            date_revocation=None
        )
        access_rights.append(ar)

# Doublon volontaire : même appli/role attribué deux fois à la même identité
if identities:
    dup_ident = identities[0]
    access_rights.append(AccessRight(
        identifiant_si=dup_ident.identifiant_si,
        application="SEMAFORE",
        role="lecture",
        date_attribution=datetime.utcnow(),
        date_revocation=None
    ))
    access_rights.append(AccessRight(
        identifiant_si=dup_ident.identifiant_si,
        application="SEMAFORE",
        role="lecture",
        date_attribution=datetime.utcnow(),
        date_revocation=None
    ))

session.add_all(access_rights)
session.commit()

# 4. Flux log — simulate un batch source -> integre -> diffuse avec un ECART volontaire
flux_runs = [
    ("RH_TO_SEMAFORE", 100, 100, 98),   # source=100, integre=100, diffuse=98 -> anomalie
    ("AD_TO_SEMAFORE", 95, 95, 95),      # OK
    ("PAIE_TO_SEMAFORE", 100, 97, 97),   # source=100, integre=97 -> anomalie a l'integration
]

for flux_nom, nb_source, nb_integre, nb_diffuse in flux_runs:
    base_date = datetime.utcnow() - timedelta(days=1)
    session.add(FluxLog(flux_nom=flux_nom, etape="source", nb_lignes=nb_source,
                         date_traitement=base_date, statut="OK"))
    session.add(FluxLog(flux_nom=flux_nom, etape="integre", nb_lignes=nb_integre,
                         date_traitement=base_date + timedelta(minutes=5),
                         statut="OK" if nb_integre == nb_source else "PARTIEL"))
    session.add(FluxLog(flux_nom=flux_nom, etape="diffuse", nb_lignes=nb_diffuse,
                         date_traitement=base_date + timedelta(minutes=10),
                         statut="OK" if nb_diffuse == nb_integre else "PARTIEL"))

session.commit()
session.close()

print(f"Données injectées : {len(employees)} employés, {len(identities)} identités, "
      f"{len(access_rights)} droits d'accès, {len(flux_runs)} flux (9 lignes flux_log)")