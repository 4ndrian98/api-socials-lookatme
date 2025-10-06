"""
TripAdvisor API Integration Service

Integra le API di TripAdvisor per raccogliere:
- Recensioni e rating di location
- Dettagli di business/location 
"""
import requests
import logging
import os
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TripAdvisorService:
    def __init__(self):
        self.api_key = os.getenv("TRIPADVISOR_API_KEY")
        self.base_url = "https://api.content.tripadvisor.com/api/v1"
        
        if not self.api_key:
            logger.warning("TRIPADVISOR_API_KEY non configurata")
    
    def extract_location_id(self, url: str) -> Optional[str]:
        """
        Estrae location ID dall'URL di TripAdvisor
        Es: https://www.tripadvisor.com/Restaurant_Review-g187849-d123456-Reviews -> 123456
        """
        try:
            parts = url.split('-')
            for part in parts:
                if part.startswith('d') and part[1:].isdigit():
                    return part[1:]  # Rimuovi 'd' e restituisci solo il numero
            
            # Fallback: cerca pattern numerico
            import re
            pattern = r'd(\d+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
                
            return None
        except Exception as e:
            logger.error(f"Errore estrazione location_id da URL {url}: {e}")
            return None
    
    def get_location_reviews(self, location_id: str, language: str = "it") -> Dict:
        """
        Ottiene le recensioni di una location da TripAdvisor
        
        Args:
            location_id: ID della location TripAdvisor
            language: Lingua delle recensioni (default: it)
            
        Returns:
            Dict con dati delle recensioni
        """
        try:
            url = f"{self.base_url}/location/{location_id}/reviews"
            headers = {
                "accept": "application/json",
                "X-TripAdvisor-API-Key": self.api_key
            }
            params = {"language": language}
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": data,
                    "reviews_count": len(data.get("data", [])),
                    "extracted_at": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Errore API TripAdvisor Reviews: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            logger.error(f"Errore chiamata TripAdvisor Reviews API: {e}")
            return {
                "success": False,
                "error": "Connection Error",
                "message": str(e)
            }
    
    def get_location_details(self, location_id: str, language: str = "it", currency: str = "EUR") -> Dict:
        """
        Ottiene i dettagli di una location da TripAdvisor
        
        Args:
            location_id: ID della location TripAdvisor
            language: Lingua dei dettagli (default: it)
            currency: Valuta per prezzi (default: EUR)
            
        Returns:
            Dict con dati della location
        """
        try:
            url = f"{self.base_url}/location/{location_id}/details"
            headers = {
                "accept": "application/json",
                "X-TripAdvisor-API-Key": self.api_key
            }
            params = {
                "language": language,
                "currency": currency
            }
            
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": data,
                    "extracted_at": datetime.utcnow().isoformat()
                }
            else:
                logger.error(f"Errore API TripAdvisor Details: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"API Error: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            logger.error(f"Errore chiamata TripAdvisor Details API: {e}")
            return {
                "success": False,
                "error": "Connection Error",
                "message": str(e)
            }
    
    def get_combined_data(self, location_id: str) -> Dict:
        """
        Ottiene sia recensioni che dettagli di una location
        
        Returns:
            Dict combinato con tutti i dati
        """
        try:
            reviews = self.get_location_reviews(location_id)
            details = self.get_location_details(location_id)
            
            # Estrai metriche chiave
            extracted_data = {
                "location_id": location_id,
                "extracted_at": datetime.utcnow().isoformat(),
                "success": reviews["success"] and details["success"]
            }
            
            if reviews["success"]:
                reviews_data = reviews["data"]
                extracted_data.update({
                    "reviews_count": len(reviews_data.get("data", [])),
                    "reviews": reviews_data.get("data", [])[:5]  # Prime 5 recensioni
                })
            
            if details["success"]:
                details_data = details["data"]
                extracted_data.update({
                    "name": details_data.get("name"),
                    "rating": details_data.get("rating"),
                    "num_reviews": details_data.get("num_reviews"),
                    "address": details_data.get("address"),
                    "phone": details_data.get("phone"),
                    "website": details_data.get("website")
                })
            
            # Aggiungi dati raw per debug
            extracted_data["raw_reviews"] = reviews
            extracted_data["raw_details"] = details
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Errore combinazione dati TripAdvisor: {e}")
            return {
                "success": False,
                "error": "Processing Error", 
                "message": str(e)
            }
    
    def extract_metrics_for_integration(self, tripadvisor_data: Dict) -> Dict:
        """
        Estrae le metriche chiave per integrazione con database esercenti
        
        Returns:
            Dict con metriche per aggiornamento database
        """
        try:
            metrics = {}
            
            if tripadvisor_data.get("success"):
                # Rating (stelle)
                if "rating" in tripadvisor_data:
                    metrics["tripadvisor_rating"] = float(tripadvisor_data["rating"])
                
                # Numero recensioni
                if "num_reviews" in tripadvisor_data:
                    metrics["tripadvisor_reviews"] = int(tripadvisor_data["num_reviews"])
                elif "reviews_count" in tripadvisor_data:
                    metrics["tripadvisor_reviews"] = int(tripadvisor_data["reviews_count"])
                
                # Timestamp aggiornamento
                metrics["last_updated"] = datetime.utcnow()
                
            return metrics
            
        except Exception as e:
            logger.error(f"Errore estrazione metriche TripAdvisor: {e}")
            return {}


# Istanza globale del servizio
tripadvisor_service = TripAdvisorService()