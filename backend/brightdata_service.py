import os
import requests
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import BrightDataJob, BrightDataResult, EsercenteSocialMapping, WeeklyCrawlSchedule
import schemas
import logging

logger = logging.getLogger(__name__)

class BrightDataService:
    def __init__(self):
        self.api_token = os.getenv("BRIGHTDATA_API_TOKEN")
        self.base_url = os.getenv("BRIGHTDATA_BASE_URL", "https://api.brightdata.com/datasets/v3")
        self.dataset_ids = {
            "instagram": os.getenv("BRIGHTDATA_INSTAGRAM_DATASET", "gd_l1vikfch901nx3by4"),
            "facebook": os.getenv("BRIGHTDATA_FACEBOOK_DATASET", "gd_m0dtqpiu1mbcyc2g86"),
            "googlemaps": os.getenv("BRIGHTDATA_GOOGLEMAPS_DATASET", "gd_luzfs1dn2oa0teb81")
        }
        
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    def trigger_crawl(self, platform: str, urls: List[str], params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Trigger a crawl job on Bright Data
        """
        if platform not in self.dataset_ids:
            raise ValueError(f"Platform {platform} not supported. Supported: {list(self.dataset_ids.keys())}")
        
        dataset_id = self.dataset_ids[platform]
        
        # Prepara i dati per la richiesta
        crawl_data = []
        for url in urls:
            if platform == "facebook" and params and "num_of_reviews" in params:
                crawl_data.append({
                    "url": url,
                    "num_of_reviews": params.get("num_of_reviews", 20)
                })
            elif platform == "googlemaps" and params and "days_limit" in params:
                crawl_data.append({
                    "url": url,
                    "days_limit": params.get("days_limit", 30)
                })
            else:
                crawl_data.append({"url": url})
        
        # Parametri della richiesta
        request_params = {
            "dataset_id": dataset_id,
            "include_errors": "true"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/trigger",
                headers=self.headers,
                params=request_params,
                json=crawl_data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Il job ID è generalmente nella risposta, se non c'è ne creiamo uno
            job_id = result.get("snapshot_id", str(uuid.uuid4()))
            
            return {
                "success": True,
                "job_id": job_id,
                "dataset_id": dataset_id,
                "platform": platform,
                "urls_count": len(urls),
                "response": result
            }
            
        except requests.RequestException as e:
            logger.error(f"Error triggering crawl for {platform}: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": platform,
                "urls_count": len(urls)
            }
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Ottieni lo status di un job
        """
        try:
            response = requests.get(
                f"{self.base_url}/snapshot/{job_id}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 404:
                return {"status": "not_found", "job_id": job_id}
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "job_id": job_id,
                "status": result.get("status", "unknown"),
                "progress": result.get("progress", {}),
                "total_rows": result.get("total_rows", 0),
                "response": result
            }
            
        except requests.RequestException as e:
            logger.error(f"Error getting job status {job_id}: {e}")
            return {
                "status": "error",
                "job_id": job_id,
                "error": str(e)
            }
    
    def get_job_results(self, job_id: str, format: str = "json") -> Dict[str, Any]:
        """
        Recupera i risultati di un job completato
        """
        try:
            response = requests.get(
                f"{self.base_url}/snapshot/{job_id}",
                headers=self.headers,
                params={"format": format},
                timeout=60
            )
            
            response.raise_for_status()
            
            if format == "json":
                return {
                    "success": True,
                    "job_id": job_id,
                    "data": response.json()
                }
            else:
                return {
                    "success": True,
                    "job_id": job_id,
                    "data": response.text
                }
            
        except requests.RequestException as e:
            logger.error(f"Error getting job results {job_id}: {e}")
            return {
                "success": False,
                "job_id": job_id,
                "error": str(e)
            }
    
    def save_job_to_db(self, db: Session, platform: str, urls: List[str], 
                      params: Dict[str, Any], response: Dict[str, Any]) -> BrightDataJob:
        """
        Salva un job nel database
        """
        job = BrightDataJob(
            job_id=response.get("job_id", str(uuid.uuid4())),
            dataset_type=platform,
            dataset_id=self.dataset_ids[platform],
            status="triggered",
            parameters={
                "urls": urls,
                "params": params
            }
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    
    def save_results_to_db(self, db: Session, job: BrightDataJob, results_data: List[Dict[str, Any]]):
        """
        Salva i risultati nel database ed estrae i dati rilevanti
        """
        for item in results_data:
            # Estrazione dati base
            source_url = item.get("url", "")
            platform = job.dataset_type
            
            # Estrazione dati specifici per platform
            followers_count = None
            posts_count = None
            reviews_count = None
            rating = None
            
            if platform == "instagram":
                followers_count = item.get("followers", item.get("follower_count"))
                posts_count = item.get("posts", item.get("media_count"))
            
            elif platform == "facebook":
                followers_count = item.get("fans", item.get("fan_count"))
                reviews_count = len(item.get("reviews", []))
                if item.get("rating"):
                    rating = float(item.get("rating", 0))
            
            elif platform == "googlemaps":
                reviews_count = item.get("reviews_count", len(item.get("reviews", [])))
                if item.get("rating"):
                    rating = float(item.get("rating", 0))
            
            # Crea il record del risultato
            result = BrightDataResult(
                job_id=job.id,
                source_url=source_url,
                platform=platform,
                raw_data=item,
                followers_count=followers_count,
                posts_count=posts_count,
                reviews_count=reviews_count,
                rating=rating
            )
            
            db.add(result)
        
        # Aggiorna il job
        job.result_count = len(results_data)
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        
        db.commit()
    
    def integrate_with_esercenti(self, db: Session, job: BrightDataJob):
        """
        Integra automaticamente i dati crawlati con gli esercenti esistenti
        """
        from models import DatoCrawled, Esercente
        from datetime import date
        
        # Trova le mappings per questo job
        results = db.query(BrightDataResult).filter(
            BrightDataResult.job_id == job.id,
            BrightDataResult.processed == "pending"
        ).all()
        
        for result in results:
            # Trova l'esercente mappato per questo URL
            mapping = db.query(EsercenteSocialMapping).filter(
                EsercenteSocialMapping.url == result.source_url,
                EsercenteSocialMapping.platform == result.platform,
                EsercenteSocialMapping.is_active == "true"
            ).first()
            
            if mapping:
                # Crea o aggiorna i dati crawlati
                today = date.today()
                existing = db.query(DatoCrawled).filter(
                    DatoCrawled.id_esercente == mapping.id_esercente,
                    DatoCrawled.data == today
                ).first()
                
                if not existing:
                    dato = DatoCrawled(
                        id_esercente=mapping.id_esercente,
                        data=today,
                        ora=datetime.now().time()
                    )
                    db.add(dato)
                else:
                    dato = existing
                
                # Aggiorna i campi in base al platform
                if result.platform == "instagram" and result.followers_count:
                    dato.n_followers_ig = result.followers_count
                elif result.platform == "facebook" and result.followers_count:
                    dato.n_fan_facebook = result.followers_count
                elif result.platform == "googlemaps" and result.rating:
                    dato.stelle_google = result.rating
                
                # Marca il risultato come processato
                result.processed = "integrated"
                
                # Aggiorna last_crawled per il mapping
                mapping.last_crawled = datetime.utcnow()
        
        db.commit()

brightdata_service = BrightDataService()