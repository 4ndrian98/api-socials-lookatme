from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, date
from database import SessionLocal, engine
import models
import schemas
from auth import authenticate, create_access_token, hash_password, get_db
from services import compute_sentiment, sentiment_trend, build_suggestions
from fastapi.middleware.cors import CORSMiddleware
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

# Avvia lo scheduler settimanale
from weekly_scheduler import weekly_scheduler

@app.on_event("startup")
def start_scheduler():
    weekly_scheduler.start_all_schedules()
    logger.info("Weekly scheduler started successfully")

@app.on_event("shutdown")
def stop_scheduler():
    weekly_scheduler.stop()
    logger.info("Weekly scheduler stopped")

# configurazione CORS
origins = [
    "http://localhost:3000",   # se usi React dev server
    "http://127.0.0.1:3000",
    "http://localhost:8080",   # se usi Vue/Angular
    "http://127.0.0.1:8080",
    # aggiungi qui altri domini autorizzati
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- SECURITY: Bearer Token ---
security = HTTPBearer()

def require_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # qui puoi validare il token con la tua logica (jwt decode, ecc.)
    if not token:
        raise HTTPException(status_code=401, detail="Token mancante o non valido")
    return token


# helper in cima a main.py (sotto gli import)
def apply_updates(instance, data: dict):
    for k, v in data.items():
        if v is not None:
            setattr(instance, k, v)


# ---------- Startup: seed utente admin ----------
@app.on_event("startup")
def seed_user():
    db = SessionLocal()
    try:
        if not db.query(models.User).first():
            db.add(models.User(email="admin@example.com", password_hash=hash_password("admin")))
            db.commit()
            print("Creato utente di test: admin@example.com / admin")
    finally:
        db.close()


# ---------- /get-token ----------
@app.post("/get-token", response_model=schemas.TokenOut)
def get_token(payload: schemas.LoginIn = Body(...), db: Session = Depends(get_db)):
    if not authenticate(db, payload.email, payload.password):
        raise HTTPException(401, "Credenziali non valide")
    return {"token": create_access_token(sub=payload.email)}


# ---------- /esercenti ----------
@app.get("/esercenti", response_model=list[schemas.Esercente])
def lista_esercenti(token: str = Depends(require_token), db: Session = Depends(get_db)):
    return db.query(models.Esercente).all()


@app.post("/esercenti", response_model=schemas.Esercente)
def crea_esercente(payload: schemas.EsercenteCreate, token: str = Depends(require_token), db: Session = Depends(get_db)):
    row = models.Esercente(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@app.patch("/esercenti/{id_esercente}", response_model=schemas.Esercente)
def update_esercente(
    id_esercente: int,
    payload: schemas.EsercenteUpdate,
    token: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    row = db.get(models.Esercente, id_esercente)
    if not row:
        raise HTTPException(404, "Esercente non trovato")
    apply_updates(row, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(row)
    return row


# ---------- /data-crawled ----------
@app.post("/data-crawled")
def crea_dato(payload: schemas.DatoCrawledCreate, token: str = Depends(require_token), db: Session = Depends(get_db)):
    now = datetime.now()
    if payload.data is None:
        payload.data = date.today()
    if payload.ora is None:
        payload.ora = now.time().replace(microsecond=0)
    row = models.DatoCrawled(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


# ---------- /rilevazione ----------
@app.post("/rilevazione")
def crea_rilevazione(payload: schemas.RilevazioneCreate, token: str = Depends(require_token), db: Session = Depends(get_db)):
    row = models.Rilevazione(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id}


# ---------- /vetrina ----------
@app.get("/vetrina", response_model=schemas.VetrinaOut)
def vetrina(id_esercente: int, token: str = Depends(require_token), db: Session = Depends(get_db)):
    e = db.get(models.Esercente, id_esercente)
    if not e:
        raise HTTPException(404, "Esercente non trovato")

    last_crawled = (db.query(models.DatoCrawled)
                      .filter(models.DatoCrawled.id_esercente == id_esercente)
                      .order_by(models.DatoCrawled.data.desc().nullslast(),
                                models.DatoCrawled.ora.desc().nullslast())
                      .first())
    last_ril = (db.query(models.Rilevazione)
                  .filter(models.Rilevazione.id_esercente == id_esercente)
                  .order_by(models.Rilevazione.id.desc())
                  .first())

    sent = compute_sentiment(last_ril)
    msg = ("Ottimo andamento!" if sent and sent >= 0.7
           else "Situazione da monitorare" if sent and sent >= 0.5
           else "Attiva azioni correttive")

    return {
        "nome": e.nome,
        "logo": e.logo,
        "colore_sfondo": e.colore_sfondo,
        "colore_carattere": e.colore_carattere,
        "n_fan_facebook": int(last_crawled.n_fan_facebook) if last_crawled else None,
        "n_followers_ig": int(last_crawled.n_followers_ig) if last_crawled else None,
        "stelle_google": last_crawled.stelle_google if last_crawled else None,
        "tripadvisor_rating": last_crawled.tripadvisor_rating if last_crawled else None,
        "tripadvisor_reviews": int(last_crawled.tripadvisor_reviews) if last_crawled and last_crawled.tripadvisor_reviews else None,
        "certificazione_1": e.certificazione_1,
        "immagine_certificazione_1": e.immagine_certificazione_1,
        "certificazione_2": e.certificazione_2,
        "immagine_certificazione_2": e.immagine_certificazione_2,
        "messaggio": msg,
        "sentiment": sent,
    }


# ---------- /dashboard ----------
@app.get("/dashboard", response_model=schemas.DashboardOut)
def dashboard(id_esercente: int, token: str = Depends(require_token), db: Session = Depends(get_db)):
    e = db.get(models.Esercente, id_esercente)
    if not e:
        raise HTTPException(404, "Esercente non trovato")

    last_crawled = (db.query(models.DatoCrawled)
                      .filter(models.DatoCrawled.id_esercente == id_esercente)
                      .order_by(models.DatoCrawled.data.desc().nullslast(),
                                models.DatoCrawled.ora.desc().nullslast())
                      .first())
    rilevazioni = (db.query(models.Rilevazione)
                     .filter(models.Rilevazione.id_esercente == id_esercente)
                     .order_by(models.Rilevazione.id.asc())
                     .all())
    sent = compute_sentiment(rilevazioni[-1] if rilevazioni else None)
    trend = sentiment_trend(rilevazioni, last_n=7)
    tips = build_suggestions(sent, trend)

    return {
        "nome": e.nome,
        "logo": e.logo,
        "n_fan_facebook": int(last_crawled.n_fan_facebook) if last_crawled else None,
        "n_followers_ig": int(last_crawled.n_followers_ig) if last_crawled else None,
        "stelle_google": last_crawled.stelle_google if last_crawled else None,
        "tripadvisor_rating": last_crawled.tripadvisor_rating if last_crawled else None,
        "tripadvisor_reviews": int(last_crawled.tripadvisor_reviews) if last_crawled and last_crawled.tripadvisor_reviews else None,
        "certificazione_1": e.certificazione_1,
        "immagine_certificazione_1": e.immagine_certificazione_1,
        "certificazione_2": e.certificazione_2,
        "immagine_certificazione_2": e.immagine_certificazione_2,
        "messaggio": "Sintesi automatica in base a sentiment e trend",
        "sentiment": sent,
        "andamento_sentiment": trend,
        "suggerimenti": tips,
    }

# ---------- BRIGHT DATA INTEGRATION ENDPOINTS ----------

from brightdata_service import brightdata_service
from models import BrightDataJob, BrightDataResult, EsercenteSocialMapping, WeeklyCrawlSchedule
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

@app.post("/api/brightdata/trigger", response_model=schemas.TriggerCrawlResponse)
def trigger_brightdata_crawl(
    payload: schemas.TriggerCrawlRequest,
    token: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    """
    Avvia un job di crawling su Bright Data
    """
    try:
        # Trigger del crawl
        response = brightdata_service.trigger_crawl(
            platform=payload.platform,
            urls=payload.urls,
            params=payload.params or {}
        )
        
        if not response.get("success"):
            raise HTTPException(500, f"Errore nel trigger crawl: {response.get('error')}")
        
        # Salva il job nel database
        job = brightdata_service.save_job_to_db(
            db=db,
            platform=payload.platform,
            urls=payload.urls,
            params=payload.params or {},
            response=response
        )
        
        return schemas.TriggerCrawlResponse(
            job_id=job.job_id,
            message=f"Crawl avviato con successo per {payload.platform}",
            dataset_type=payload.platform,
            url_count=len(payload.urls)
        )
        
    except Exception as e:
        raise HTTPException(500, f"Errore interno: {str(e)}")


@app.get("/api/brightdata/status/{job_id}", response_model=schemas.CrawlStatusResponse)
def get_crawl_status(
    job_id: str,
    token: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    """
    Ottieni lo status di un job di crawling
    """
    # Verifica il job nel database
    job = db.query(BrightDataJob).filter(BrightDataJob.job_id == job_id).first()
    if not job:
        raise HTTPException(404, "Job non trovato")
    
    # Ottieni status da Bright Data
    status_response = brightdata_service.get_job_status(job_id)
    
    # Aggiorna il job nel database se necessario
    if status_response.get("status") in ["completed", "failed"]:
        job.status = status_response["status"]
        if status_response["status"] == "completed":
            job.completed_at = datetime.utcnow()
        db.commit()
    
    return schemas.CrawlStatusResponse(
        job_id=job_id,
        status=status_response.get("status", "unknown"),
        progress=status_response.get("progress", {}),
        results_available=status_response.get("status") == "completed"
    )


@app.get("/api/brightdata/results/{job_id}")
def get_crawl_results(
    job_id: str,
    auto_integrate: bool = True,
    token: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    """
    Recupera e salva i risultati di un job completato
    """
    # Verifica il job nel database
    job = db.query(BrightDataJob).filter(BrightDataJob.job_id == job_id).first()
    if not job:
        raise HTTPException(404, "Job non trovato")
    
    if job.status != "completed":
        # Prova a controllare lo status
        status_response = brightdata_service.get_job_status(job_id)
        if status_response.get("status") != "completed":
            raise HTTPException(400, "Job non ancora completato")
    
    # Recupera i risultati da Bright Data
    results_response = brightdata_service.get_job_results(job_id)
    
    if not results_response.get("success"):
        raise HTTPException(500, f"Errore nel recupero risultati: {results_response.get('error')}")
    
    results_data = results_response.get("data", [])
    
    # Salva i risultati nel database
    brightdata_service.save_results_to_db(db, job, results_data)
    
    # Integrazione automatica con esercenti se richiesta
    if auto_integrate:
        brightdata_service.integrate_with_esercenti(db, job)
    
    return {
        "job_id": job_id,
        "results_count": len(results_data),
        "status": "processed",
        "integrated": auto_integrate
    }


@app.post("/api/brightdata/social-mapping")
def create_social_mapping(
    payload: schemas.SocialMappingRequest,
    token: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    """
    Crea mappature tra esercenti e URL social per crawling automatico
    """
    # Verifica che l'esercente esista
    esercente = db.get(models.Esercente, payload.id_esercente)
    if not esercente:
        raise HTTPException(404, "Esercente non trovato")
    
    created_mappings = []
    
    for mapping_data in payload.mappings:
        # Controlla se esiste già
        existing = db.query(EsercenteSocialMapping).filter(
            EsercenteSocialMapping.id_esercente == payload.id_esercente,
            EsercenteSocialMapping.platform == mapping_data["platform"],
            EsercenteSocialMapping.url == mapping_data["url"]
        ).first()
        
        if not existing:
            mapping = EsercenteSocialMapping(
                id_esercente=payload.id_esercente,
                platform=mapping_data["platform"],
                url=mapping_data["url"],
                crawl_params=mapping_data.get("params", {})
            )
            db.add(mapping)
            created_mappings.append(mapping_data)
    
    db.commit()
    
    return {
        "esercente_id": payload.id_esercente,
        "mappings_created": len(created_mappings),
        "mappings": created_mappings
    }


@app.get("/api/brightdata/social-mapping/{id_esercente}")
def get_social_mappings(
    id_esercente: int,
    token: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    """
    Ottieni le mappature social di un esercente
    """
    mappings = db.query(EsercenteSocialMapping).filter(
        EsercenteSocialMapping.id_esercente == id_esercente
    ).all()
    
    return {
        "esercente_id": id_esercente,
        "mappings": [
            {
                "id": m.id,
                "platform": m.platform,
                "url": m.url,
                "params": m.crawl_params,
                "is_active": m.is_active,
                "last_crawled": m.last_crawled
            }
            for m in mappings
        ]
    }


@app.post("/api/brightdata/weekly-crawl")
def trigger_weekly_crawl(
    token: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    """
    Avvia il crawl settimanale di tutti gli esercenti con mappature attive
    """
    from datetime import date
    
    # Calcola il lunedì di questa settimana
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    # Controlla se il crawl settimanale è già stato avviato
    existing_schedule = db.query(WeeklyCrawlSchedule).filter(
        WeeklyCrawlSchedule.week_start == week_start,
        WeeklyCrawlSchedule.status.in_(["pending", "running"])
    ).first()
    
    if existing_schedule:
        return {
            "message": "Crawl settimanale già in corso per questa settimana",
            "schedule_id": existing_schedule.id,
            "week_start": week_start
        }
    
    # Crea il record di schedulazione
    schedule = WeeklyCrawlSchedule(
        week_start=week_start,
        status="running",
        triggered_at=datetime.utcnow()
    )
    db.add(schedule)
    db.commit()
    
    # Ottieni tutte le mappature attive
    active_mappings = db.query(EsercenteSocialMapping).filter(
        EsercenteSocialMapping.is_active == "true"
    ).all()
    
    # Raggruppa per platform
    platform_urls = {}
    for mapping in active_mappings:
        if mapping.platform not in platform_urls:
            platform_urls[mapping.platform] = []
        
        url_data = {"url": mapping.url}
        if mapping.crawl_params:
            url_data.update(mapping.crawl_params)
        
        platform_urls[mapping.platform].append(url_data)
    
    # Avvia i job per ogni platform
    triggered_jobs = []
    for platform, urls_data in platform_urls.items():
        urls = [item["url"] for item in urls_data]
        params = urls_data[0] if urls_data else {}
        params.pop("url", None)  # Rimuovi url dai params se presente
        
        try:
            response = brightdata_service.trigger_crawl(
                platform=platform,
                urls=urls,
                params=params
            )
            
            if response.get("success"):
                # Salva il job nel database
                job = brightdata_service.save_job_to_db(
                    db=db,
                    platform=platform,
                    urls=urls,
                    params=params,
                    response=response
                )
                triggered_jobs.append({
                    "platform": platform,
                    "job_id": job.job_id,
                    "urls_count": len(urls)
                })
        
        except Exception as e:
            logger.error(f"Error triggering weekly crawl for {platform}: {e}")
    
    # Aggiorna il schedule
    schedule.total_jobs = len(triggered_jobs)
    db.commit()
    
    return {
        "message": f"Crawl settimanale avviato con {len(triggered_jobs)} job",
        "schedule_id": schedule.id,
        "week_start": week_start,
        "jobs": triggered_jobs
    }


@app.get("/api/brightdata/weekly-crawl/status")
def get_weekly_crawl_status(
    token: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    """
    Ottieni lo status del crawl settimanale corrente
    """
    from datetime import date
    
    # Calcola il lunedì di questa settimana
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    schedule = db.query(WeeklyCrawlSchedule).filter(
        WeeklyCrawlSchedule.week_start == week_start
    ).first()
    
    if not schedule:
        return {
            "message": "Nessun crawl settimanale trovato per questa settimana",
            "week_start": week_start
        }
    
    # Ottieni i job correlati
    jobs = db.query(BrightDataJob).filter(
        BrightDataJob.created_at >= datetime.combine(week_start, datetime.min.time())
    ).all()
    
    completed_jobs = len([j for j in jobs if j.status == "completed"])
    failed_jobs = len([j for j in jobs if j.status == "failed"])
    
    return {
        "schedule_id": schedule.id,
        "week_start": week_start,
        "status": schedule.status,
        "triggered_at": schedule.triggered_at,
        "completed_at": schedule.completed_at,
        "total_jobs": schedule.total_jobs,
        "completed_jobs": completed_jobs,
        "failed_jobs": failed_jobs,
        "jobs": [
            {
                "job_id": j.job_id,
                "platform": j.dataset_type,
                "status": j.status,
                "result_count": j.result_count
            }
            for j in jobs
        ]
    }

# ---------- TRIPADVISOR INTEGRATION ENDPOINTS ----------

from tripadvisor_service import tripadvisor_service

@app.post("/api/tripadvisor/crawl", response_model=schemas.TripAdvisorResponse)
def crawl_tripadvisor(
    payload: schemas.TripAdvisorCrawlRequest,
    token: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    """
    Crawl TripAdvisor data per una location
    """
    try:
        # Estrai location_id dall'URL
        location_id = tripadvisor_service.extract_location_id(payload.tripadvisor_url)
        
        if not location_id:
            raise HTTPException(400, "Impossibile estrarre location_id dall'URL TripAdvisor")
        
        # Ottieni i dati combinati
        combined_data = tripadvisor_service.get_combined_data(location_id)
        
        if not combined_data.get("success"):
            return schemas.TripAdvisorResponse(
                success=False,
                error=combined_data.get("error"),
                message=combined_data.get("message")
            )
        
        return schemas.TripAdvisorResponse(
            success=True,
            location_id=location_id,
            name=combined_data.get("name"),
            rating=combined_data.get("rating"),
            reviews_count=combined_data.get("num_reviews") or combined_data.get("reviews_count"),
            address=combined_data.get("address"),
            phone=combined_data.get("phone"),
            website=combined_data.get("website"),
            reviews=combined_data.get("reviews", [])
        )
        
    except Exception as e:
        logger.error(f"Errore crawl TripAdvisor: {e}")
        raise HTTPException(500, f"Errore interno: {str(e)}")


@app.post("/api/tripadvisor/integrate/{id_esercente}")
def integrate_tripadvisor_data(
    id_esercente: int,
    tripadvisor_url: str,
    token: str = Depends(require_token),
    db: Session = Depends(get_db)
):
    """
    Integra i dati TripAdvisor con un esercente esistente
    """
    try:
        # Verifica che l'esercente esista
        esercente = db.get(models.Esercente, id_esercente)
        if not esercente:
            raise HTTPException(404, "Esercente non trovato")
        
        # Estrai location_id dall'URL
        location_id = tripadvisor_service.extract_location_id(tripadvisor_url)
        
        if not location_id:
            raise HTTPException(400, "Impossibile estrarre location_id dall'URL TripAdvisor")
        
        # Ottieni i dati TripAdvisor
        combined_data = tripadvisor_service.get_combined_data(location_id)
        
        if not combined_data.get("success"):
            raise HTTPException(500, f"Errore nel crawl TripAdvisor: {combined_data.get('error')}")
        
        # Aggiorna l'esercente con l'URL TripAdvisor
        esercente.tripadvisor_url = tripadvisor_url
        
        # Ottieni o crea un nuovo record dati_crawled per oggi
        today = date.today()
        now = datetime.now()
        
        dato_crawled = db.query(models.DatoCrawled).filter(
            models.DatoCrawled.id_esercente == id_esercente,
            models.DatoCrawled.data == today
        ).first()
        
        if not dato_crawled:
            dato_crawled = models.DatoCrawled(
                id_esercente=id_esercente,
                data=today,
                ora=now.time().replace(microsecond=0),
                n_fan_facebook=0,
                n_followers_ig=0,
                stelle_google=None,
                tripadvisor_rating=None,
                tripadvisor_reviews=None
            )
            db.add(dato_crawled)
        
        # Aggiorna con i dati TripAdvisor
        if combined_data.get("rating"):
            dato_crawled.tripadvisor_rating = float(combined_data["rating"])
        
        if combined_data.get("num_reviews"):
            dato_crawled.tripadvisor_reviews = int(combined_data["num_reviews"])
        elif combined_data.get("reviews_count"):
            dato_crawled.tripadvisor_reviews = int(combined_data["reviews_count"])
        
        db.commit()
        db.refresh(dato_crawled)
        
        return {
            "success": True,
            "esercente_id": id_esercente,
            "location_id": location_id,
            "tripadvisor_rating": dato_crawled.tripadvisor_rating,
            "tripadvisor_reviews": dato_crawled.tripadvisor_reviews,
            "updated_at": now.isoformat(),
            "message": "Dati TripAdvisor integrati con successo"
        }
        
    except Exception as e:
        logger.error(f"Errore integrazione TripAdvisor: {e}")
        raise HTTPException(500, f"Errore interno: {str(e)}")


@app.get("/api/tripadvisor/test")
def test_tripadvisor_api(
    location_id: str = "123456",
    token: str = Depends(require_token)
):
    """
    Test endpoint per verificare che l'API TripAdvisor funzioni
    """
    try:
        # Test con location_id di esempio
        combined_data = tripadvisor_service.get_combined_data(location_id)
        
        return {
            "test_location_id": location_id,
            "api_configured": bool(tripadvisor_service.api_key),
            "api_key_present": "✅" if tripadvisor_service.api_key else "❌",
            "response": combined_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "test_location_id": location_id,
            "api_configured": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
