from fastapi import FastAPI, Depends, HTTPException, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, date
from database import SessionLocal, engine
import models, schemas
from auth import authenticate, create_access_token, hash_password, get_db
from services import compute_sentiment, sentiment_trend, build_suggestions
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

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
        "certificazione_1": e.certificazione_1,
        "immagine_certificazione_1": e.immagine_certificazione_1,
        "certificazione_2": e.certificazione_2,
        "immagine_certificazione_2": e.immagine_certificazione_2,
        "messaggio": "Sintesi automatica in base a sentiment e trend",
        "sentiment": sent,
        "andamento_sentiment": trend,
        "suggerimenti": tips,
    }
