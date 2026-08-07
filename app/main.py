from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func
from db.models import init_db, Employee, Identity, AccessRight, FluxLog

app = FastAPI(title="SEMAFORE Mock API", version="1.0")

engine = init_db()
Session = sessionmaker(bind=engine)


def get_session():
    return Session()


@app.get("/")
def root():
    return {"status": "SEMAFORE mock concentrateur - API OK"}


@app.get("/employees")
def list_employees(statut: str | None = None):
    session = get_session()
    query = session.query(Employee)
    if statut:
        query = query.filter(Employee.statut == statut)
    results = [
        {"matricule": e.matricule, "nom": e.nom, "prenom": e.prenom,
         "statut": e.statut, "date_entree": str(e.date_entree)}
        for e in query.all()
    ]
    session.close()
    return {"count": len(results), "employees": results}


@app.get("/employees/{matricule}")
def get_employee(matricule: str):
    session = get_session()
    emp = session.query(Employee).filter(Employee.matricule == matricule).first()
    session.close()
    if not emp:
        raise HTTPException(status_code=404, detail="Employé non trouvé")
    return {"matricule": emp.matricule, "nom": emp.nom, "prenom": emp.prenom,
            "statut": emp.statut, "date_entree": str(emp.date_entree)}


@app.get("/identities")
def list_identities():
    session = get_session()
    results = [
        {"matricule": i.matricule, "identifiant_si": i.identifiant_si,
         "source_systeme": i.source_systeme}
        for i in session.query(Identity).all()
    ]
    session.close()
    return {"count": len(results), "identities": results}


@app.get("/access-rights/{identifiant_si}")
def get_access_rights(identifiant_si: str):
    session = get_session()
    rights = session.query(AccessRight).filter(
        AccessRight.identifiant_si == identifiant_si
    ).all()
    session.close()
    if not rights:
        raise HTTPException(status_code=404, detail="Aucun droit trouvé pour cet identifiant")
    return {
        "identifiant_si": identifiant_si,
        "rights": [{"application": r.application, "role": r.role,
                    "date_attribution": str(r.date_attribution)} for r in rights]
    }


@app.get("/flux/status")
def flux_status():
    session = get_session()
    flux_noms = session.query(FluxLog.flux_nom).distinct().all()
    result = []
    for (nom,) in flux_noms:
        etapes = session.query(FluxLog).filter(FluxLog.flux_nom == nom).all()
        result.append({
            "flux_nom": nom,
            "etapes": [{"etape": e.etape, "nb_lignes": e.nb_lignes, "statut": e.statut}
                       for e in etapes]
        })
    session.close()
    return {"flux": result}