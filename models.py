
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Numeric, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

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
    tripadvisor_url = Column(String)
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


# --------- BRIGHT DATA INTEGRATION MODELS ---------

class BrightDataJob(Base):
    """Modello per tracciare i job di crawling Bright Data"""
    __tablename__ = "brightdata_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, nullable=False, index=True)  # ID del job da Bright Data
    dataset_type = Column(String, nullable=False)  # 'instagram', 'facebook', 'googlemaps'
    dataset_id = Column(String, nullable=False)  # ID dataset Bright Data
    status = Column(String, default="triggered")  # 'triggered', 'running', 'completed', 'failed'
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    parameters = Column(JSON)  # Parametri originali della richiesta
    result_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    
    # Relazione con i risultati
    results = relationship("BrightDataResult", back_populates="job", cascade="all, delete")


class BrightDataResult(Base):
    """Modello per memorizzare i risultati del crawling"""
    __tablename__ = "brightdata_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("brightdata_jobs.id", ondelete="CASCADE"), nullable=False)
    source_url = Column(String, nullable=False)  # URL originale crawlata
    platform = Column(String, nullable=False)  # 'instagram', 'facebook', 'googlemaps'
    raw_data = Column(JSON, nullable=False)  # Dati raw da Bright Data
    extracted_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(String, default="pending")  # 'pending', 'integrated', 'failed'
    
    # Campi estratti comuni per tutti i platform
    followers_count = Column(Integer, nullable=True)
    posts_count = Column(Integer, nullable=True)
    reviews_count = Column(Integer, nullable=True)
    rating = Column(Numeric(2, 1), nullable=True)
    
    # Relazioni
    job = relationship("BrightDataJob", back_populates="results")


class EsercenteSocialMapping(Base):
    """Mappatura tra esercenti e URL social per crawling automatico"""
    __tablename__ = "esercenti_social_mapping"
    
    id = Column(Integer, primary_key=True, index=True)
    id_esercente = Column(Integer, ForeignKey("esercenti.id_esercente", ondelete="CASCADE"), nullable=False)
    platform = Column(String, nullable=False)  # 'instagram', 'facebook', 'googlemaps'
    url = Column(String, nullable=False)
    is_active = Column(String, default="true")  # 'true', 'false'
    created_at = Column(DateTime, default=datetime.utcnow)
    last_crawled = Column(DateTime, nullable=True)
    
    # Parametri specifici per platform
    crawl_params = Column(JSON, nullable=True)  # es. num_of_reviews per Facebook
    
    # Relazione con esercente
    esercente = relationship("Esercente")


class WeeklyCrawlSchedule(Base):
    """Schedulazione settimanale dei crawl"""
    __tablename__ = "weekly_crawl_schedule"
    
    id = Column(Integer, primary_key=True, index=True)
    week_start = Column(Date, nullable=False)  # Lunedì della settimana
    status = Column(String, default="pending")  # 'pending', 'running', 'completed', 'failed'
    triggered_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_jobs = Column(Integer, default=0)
    completed_jobs = Column(Integer, default=0)
    failed_jobs = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
