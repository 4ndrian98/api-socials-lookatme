from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import date, time, datetime
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
    tripadvisor_url: Optional[str] = None
    certificazione_1: Optional[str] = None
    immagine_certificazione_1: Optional[str] = None
    certificazione_2: Optional[str] = None
    immagine_certificazione_2: Optional[str] = None

class EsercenteCreate(EsercenteBase): 
    pass

class EsercenteUpdate(BaseModel):
    nome: Optional[str] = None
    contatto: Optional[str] = None
    logo: Optional[str] = None
    colore_sfondo: Optional[str] = None
    colore_carattere: Optional[str] = None
    pagina_web_fb: Optional[str] = None
    pagina_ig: Optional[str] = None
    google_recensioni: Optional[str] = None
    tripadvisor_url: Optional[str] = None
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
    tripadvisor_rating: Optional[Decimal] = None
    tripadvisor_reviews: Optional[int] = None

class DatoCrawledCreate(DatoCrawledBase): 
    pass

class DatoCrawledUpdate(BaseModel):
    id_esercente: Optional[int] = None
    data: Optional[date] = None
    ora: Optional[time] = None
    n_fan_facebook: Optional[int] = None
    n_followers_ig: Optional[int] = None
    stelle_google: Optional[Decimal] = None
    tripadvisor_rating: Optional[Decimal] = None
    tripadvisor_reviews: Optional[int] = None

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

class RilevazioneCreate(RilevazioneBase): 
    pass
class RilevazioneUpdate(RilevazioneBase): 
    pass

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


# -------- BRIGHT DATA SCHEMAS --------

class BrightDataJobBase(BaseModel):
    dataset_type: str
    dataset_id: str
    parameters: Optional[Dict[str, Any]] = {}

class BrightDataJobCreate(BrightDataJobBase):
    pass

class BrightDataJob(BrightDataJobBase):
    id: int
    job_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result_count: int = 0
    error_message: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class BrightDataResultBase(BaseModel):
    source_url: str
    platform: str
    raw_data: Dict[str, Any]
    
class BrightDataResultCreate(BrightDataResultBase):
    job_id: int

class BrightDataResult(BrightDataResultBase):
    id: int
    job_id: int
    extracted_at: datetime
    processed: str = "pending"
    followers_count: Optional[int] = None
    posts_count: Optional[int] = None
    reviews_count: Optional[int] = None
    rating: Optional[Decimal] = None
    model_config = ConfigDict(from_attributes=True)

class EsercenteSocialMappingBase(BaseModel):
    id_esercente: int
    platform: str
    url: str
    crawl_params: Optional[Dict[str, Any]] = {}

class EsercenteSocialMappingCreate(EsercenteSocialMappingBase):
    pass

class EsercenteSocialMapping(EsercenteSocialMappingBase):
    id: int
    is_active: str = "true"
    created_at: datetime
    last_crawled: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class WeeklyCrawlScheduleBase(BaseModel):
    week_start: date

class WeeklyCrawlScheduleCreate(WeeklyCrawlScheduleBase):
    pass

class WeeklyCrawlSchedule(WeeklyCrawlScheduleBase):
    id: int
    status: str = "pending"
    triggered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# -------- API REQUEST/RESPONSE SCHEMAS --------

class TriggerCrawlRequest(BaseModel):
    platform: str  # 'instagram', 'facebook', 'googlemaps'
    urls: List[str]
    params: Optional[Dict[str, Any]] = {}

class TriggerCrawlResponse(BaseModel):
    job_id: str
    message: str
    dataset_type: str
    url_count: int

class CrawlStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[Dict[str, Any]] = {}
    results_available: bool = False

class SocialMappingRequest(BaseModel):
    id_esercente: int
    mappings: List[Dict[str, Any]]  # [{'platform': 'instagram', 'url': '...', 'params': {...}}]

# -------- TRIPADVISOR SCHEMAS --------

class TripAdvisorCrawlRequest(BaseModel):
    tripadvisor_url: str
    language: Optional[str] = "it"
    currency: Optional[str] = "EUR"

class TripAdvisorResponse(BaseModel):
    success: bool
    location_id: Optional[str] = None
    name: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    reviews: Optional[List[Dict]] = []
    error: Optional[str] = None
    message: Optional[str] = None