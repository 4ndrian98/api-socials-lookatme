
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Numeric
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    id_esercente = Column(Integer, ForeignKey("esercenti.id_esercente"), nullable=True)

    esercente = relationship("Esercente", backref="users")
    
# --------- ESERCENTI / DATI / RILEVAZIONI ---------
class Esercente(Base):
    __tablename__ = "esercenti"

    id_esercente = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    contatto = Column(String)
    logo = Column(String)
    colore_sfondo = Column(String)
    colore_carattere = Column(String)
    pagina_web_fb = Column(String)
    pagina_ig = Column(String)
    google_recensioni = Column(String)
    certificazione_1 = Column(String)
    immagine_certificazione_1 = Column(String)
    certificazione_2 = Column(String)
    immagine_certificazione_2 = Column(String)

    dati = relationship("DatoCrawled", back_populates="esercente", cascade="all, delete")
    rilevazioni = relationship("Rilevazione", back_populates="esercente", cascade="all, delete")

class DatoCrawled(Base):
    __tablename__ = "dati_crawled"

    id = Column(Integer, primary_key=True, index=True)
    id_esercente = Column(Integer, ForeignKey("esercenti.id_esercente", ondelete="CASCADE"), nullable=False)
    data = Column(Date)
    ora = Column(Time)
    n_fan_facebook = Column(Integer)
    n_followers_ig = Column(Integer)
    stelle_google = Column(Numeric(2, 1))

    esercente = relationship("Esercente", back_populates="dati")

class Rilevazione(Base):
    __tablename__ = "rilevazioni"

    id = Column(Integer, primary_key=True, index=True)
    id_esercente = Column(Integer, ForeignKey("esercenti.id_esercente", ondelete="CASCADE"), nullable=False)
    gioia = Column(Numeric(3, 2))
    tristezza = Column(Numeric(3, 2))
    paura = Column(Numeric(3, 2))
    rabbia = Column(Numeric(3, 2))
    disgusto = Column(Numeric(3, 2))
    sorpresa = Column(Numeric(3, 2))
    neutro = Column(Numeric(3, 2))
    n_passanti = Column(Integer)

    esercente = relationship("Esercente", back_populates="rilevazioni")
