from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, time
from decimal import Decimal

# -------- LOGIN --------
class TokenOut(BaseModel):
    token: str

class LoginIn(BaseModel):
    email: str
    password: str

# -------- ESERCEsNTI --------
class EsercenteBase(BaseModel):
    nome: str
    contatto: Optional[str] = None
    logo: Optional[str] = None
    colore_sfondo: Optional[str] = None
    colore_carattere: Optional[str] = None
    pagina_web_fb: Optional[str] = None
    pagina_ig: Optional[str] = None
    google_recensioni: Optional[str] = None
    certificazione_1: Optional[str] = None
    immagine_certificazione_1: Optional[str] = None
    certificazione_2: Optional[str] = None
    immagine_certificazione_2: Optional[str] = None

class EsercenteCreate(EsercenteBase): pass

class EsercenteUpdate(BaseModel):
    nome: Optional[str] = None
    contatto: Optional[str] = None
    logo: Optional[str] = None
    colore_sfondo: Optional[str] = None
    colore_carattere: Optional[str] = None
    pagina_web_fb: Optional[str] = None
    pagina_ig: Optional[str] = None
    google_recensioni: Optional[str] = None
    certificazione_1: Optional[str] = None
    immagine_certificazione_1: Optional[str] = None
    certificazione_2: Optional[str] = None
    immagine_certificazione_2: Optional[str] = None

class Esercente(EsercenteBase):
    id_esercente: int
    model_config = ConfigDict(from_attributes=True)

# -------- DATI CRAWLED --------
class DatoCrawledBase(BaseModel):
    id_esercente: int
    data: Optional[date] = None
    ora: Optional[time] = None
    n_fan_facebook: Optional[int] = 0
    n_followers_ig: Optional[int] = 0
    stelle_google: Optional[Decimal] = None

class DatoCrawledCreate(DatoCrawledBase): pass

class DatoCrawledUpdate(BaseModel):
    id_esercente: Optional[int] = None
    data: Optional[date] = None
    ora: Optional[time] = None
    n_fan_facebook: Optional[int] = None
    n_followers_ig: Optional[int] = None
    stelle_google: Optional[Decimal] = None

class DatoCrawled(DatoCrawledBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# -------- RILEVAZIONI --------
class RilevazioneBase(BaseModel):
    id_esercente: int
    gioia: Optional[Decimal] = None
    tristezza: Optional[Decimal] = None
    paura: Optional[Decimal] = None
    rabbia: Optional[Decimal] = None
    disgusto: Optional[Decimal] = None
    sorpresa: Optional[Decimal] = None
    neutro: Optional[Decimal] = None
    n_passanti: Optional[int] = None

class RilevazioneCreate(RilevazioneBase): pass
class RilevazioneUpdate(RilevazioneBase): pass

class Rilevazione(RilevazioneBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# -------- OUTPUT compositi --------
class VetrinaOut(BaseModel):
    nome: Optional[str]
    logo: Optional[str]
    colore_sfondo: Optional[str]
    colore_carattere: Optional[str]
    n_fan_facebook: Optional[int]
    n_followers_ig: Optional[int]
    stelle_google: Optional[Decimal]
    certificazione_1: Optional[str]
    immagine_certificazione_1: Optional[str]
    certificazione_2: Optional[str]
    immagine_certificazione_2: Optional[str]
    certificazione_3: Optional[str] = None              # non presente a DB -> None
    immagine_certificazione_3: Optional[str] = None     # non presente a DB -> None
    messaggio: Optional[str]
    sentiment: Optional[float]

class DashboardOut(VetrinaOut):
    andamento_sentiment: list[float] = []
    suggerimenti: list[str] = []
