from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    matricule = Column(String, unique=True, nullable=False)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    date_entree = Column(Date, nullable=False)
    statut = Column(String, nullable=False)  # actif, sorti, suspendu

class Identity(Base):
    __tablename__ = "identities"
    id = Column(Integer, primary_key=True)
    matricule = Column(String, ForeignKey("employees.matricule"), nullable=False)
    identifiant_si = Column(String, unique=True, nullable=False)
    source_systeme = Column(String, nullable=False)  # ex: "RH_SOURCE", "AD"
    date_creation = Column(DateTime, nullable=False)

class AccessRight(Base):
    __tablename__ = "access_rights"
    id = Column(Integer, primary_key=True)
    identifiant_si = Column(String, ForeignKey("identities.identifiant_si"), nullable=False)
    application = Column(String, nullable=False)
    role = Column(String, nullable=False)
    date_attribution = Column(DateTime, nullable=False)
    date_revocation = Column(DateTime, nullable=True)

class FluxLog(Base):
    __tablename__ = "flux_log"
    id = Column(Integer, primary_key=True)
    flux_nom = Column(String, nullable=False)  # ex: "RH_TO_SEMAFORE"
    etape = Column(String, nullable=False)  # "source", "integre", "diffuse"
    nb_lignes = Column(Integer, nullable=False)
    date_traitement = Column(DateTime, default=datetime.utcnow)
    statut = Column(String, nullable=False)  # "OK", "KO", "PARTIEL"

def init_db(db_path="db/semafore.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine

if __name__ == "__main__":
    init_db()
    print("Base initialisée avec succès")