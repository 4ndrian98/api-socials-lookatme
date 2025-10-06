#!/usr/bin/env python3
"""
Script per testare localmente la funzionalità Bright Data
Verifica che il sistema:
1. Prelevi i link social dal database degli esercenti
2. Avvi il crawling su Bright Data
3. Scarichi i risultati (CSV/JSON)
"""

import requests
import json
import time
import sys
from typing import Dict, Any

# Configurazione
BASE_URL = "http://localhost:8001"

def get_auth_token() -> str:
    """Ottieni il token di autenticazione"""
    print("🔐 Ottenendo token di autenticazione...")
    response = requests.post(
        f"{BASE_URL}/get-token",
        json={"email": "admin@example.com", "password": "admin"}
    )
    
    if response.status_code == 200:
        token = response.json()["token"]
        print("✅ Token ottenuto con successo")
        return token
    else:
        print(f"❌ Errore nell'ottenere il token: {response.status_code}")
        print(response.text)
        sys.exit(1)

def list_esercenti(token: str) -> list:
    """Lista tutti gli esercenti"""
    print("\n📋 Recuperando lista esercenti...")
    response = requests.get(
        f"{BASE_URL}/esercenti",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        esercenti = response.json()
        print(f"✅ Trovati {len(esercenti)} esercenti")
        for e in esercenti:
            print(f"   - ID: {e['id_esercente']}, Nome: {e['nome']}")
        return esercenti
    else:
        print(f"❌ Errore nel recuperare gli esercenti: {response.status_code}")
        return []

def get_social_mappings(token: str, id_esercente: int) -> Dict[str, Any]:
    """Ottieni i mapping social di un esercente"""
    print(f"\n🔗 Recuperando mapping social per esercente ID {id_esercente}...")
    response = requests.get(
        f"{BASE_URL}/api/brightdata/social-mapping/{id_esercente}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Trovati {len(data.get('mappings', []))} mapping:")
        for m in data.get('mappings', []):
            print(f"   - Platform: {m['platform']}, URL: {m['url']}, Active: {m['is_active']}")
        return data
    else:
        print(f"❌ Errore nel recuperare i mapping: {response.status_code}")
        return {"mappings": []}

def create_test_esercente_with_mappings(token: str) -> int:
    """Crea un esercente di test con mapping social"""
    print("\n🏪 Creando esercente di test...")
    
    # Crea esercente
    esercente_data = {
        "nome": "Test Restaurant BrightData",
        "contatto": "test@example.com",
        "logo": None,
        "colore_sfondo": "#ffffff",
        "colore_carattere": "#000000"
    }
    
    response = requests.post(
        f"{BASE_URL}/esercenti",
        headers={"Authorization": f"Bearer {token}"},
        json=esercente_data
    )
    
    if response.status_code != 200:
        print(f"❌ Errore nella creazione dell'esercente: {response.status_code}")
        return None
    
    esercente = response.json()
    id_esercente = esercente["id_esercente"]
    print(f"✅ Esercente creato con ID: {id_esercente}")
    
    # Crea mapping social
    print("\n🔗 Creando mapping social...")
    mapping_data = {
        "id_esercente": id_esercente,
        "mappings": [
            {
                "platform": "instagram",
                "url": "https://www.instagram.com/italianfood",
                "params": {}
            },
            {
                "platform": "facebook",
                "url": "https://www.facebook.com/italianrestaurant",
                "params": {"num_of_reviews": 50}
            },
            {
                "platform": "googlemaps",
                "url": "https://www.google.com/maps/place/Restaurant",
                "params": {"days_limit": 30}
            }
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/brightdata/social-mapping",
        headers={"Authorization": f"Bearer {token}"},
        json=mapping_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Creati {result['mappings_created']} mapping social")
    else:
        print(f"❌ Errore nella creazione dei mapping: {response.status_code}")
    
    return id_esercente

def trigger_crawl_test(token: str, platform: str = "instagram") -> Dict[str, Any]:
    """Avvia un crawl di test"""
    print(f"\n🚀 Avviando crawl di test per {platform}...")
    
    crawl_data = {
        "platform": platform,
        "urls": ["https://www.instagram.com/italianfood"],
        "params": {}
    }
    
    response = requests.post(
        f"{BASE_URL}/api/brightdata/trigger",
        headers={"Authorization": f"Bearer {token}"},
        json=crawl_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Crawl avviato con successo!")
        print(f"   Job ID: {result['job_id']}")
        print(f"   Dataset: {result['dataset_type']}")
        print(f"   URL Count: {result['url_count']}")
        return result
    else:
        print(f"❌ Errore nell'avvio del crawl: {response.status_code}")
        print(response.text)
        return {}

def check_job_status(token: str, job_id: str) -> Dict[str, Any]:
    """Controlla lo stato di un job"""
    print(f"\n📊 Controllando stato del job {job_id}...")
    
    response = requests.get(
        f"{BASE_URL}/api/brightdata/status/{job_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code == 200:
        result = response.json()
        status = result.get("status", "unknown")
        print(f"✅ Status: {status}")
        if result.get("progress"):
            print(f"   Progress: {json.dumps(result['progress'], indent=2)}")
        return result
    else:
        print(f"❌ Errore nel controllo dello stato: {response.status_code}")
        return {}

def download_results(token: str, job_id: str) -> Dict[str, Any]:
    """Scarica i risultati di un job completato"""
    print(f"\n⬇️  Scaricando risultati del job {job_id}...")
    
    response = requests.get(
        f"{BASE_URL}/api/brightdata/results/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
        params={"auto_integrate": "true"}
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Risultati scaricati!")
        print(f"   Risultati trovati: {result.get('results_count', 0)}")
        print(f"   Integrati: {result.get('integrated', False)}")
        
        # Salva i risultati in un file
        filename = f"brightdata_results_{job_id}.json"
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"   💾 Risultati salvati in: {filename}")
        
        return result
    else:
        print(f"❌ Errore nello scaricare i risultati: {response.status_code}")
        print(response.text)
        return {}

def main():
    """Test principale"""
    print("=" * 60)
    print("🧪 TEST BRIGHT DATA INTEGRATION")
    print("=" * 60)
    
    # 1. Autenticazione
    token = get_auth_token()
    
    # 2. Lista esercenti esistenti
    esercenti = list_esercenti(token)
    
    # 3. Se non ci sono esercenti o non hanno mapping, crea uno di test
    id_esercente_test = None
    if not esercenti:
        id_esercente_test = create_test_esercente_with_mappings(token)
    else:
        # Usa il primo esercente
        id_esercente_test = esercenti[0]["id_esercente"]
        mappings = get_social_mappings(token, id_esercente_test)
        
        # Se non ha mapping, creali
        if not mappings.get("mappings"):
            print(f"\n⚠️  Esercente {id_esercente_test} non ha mapping social")
            create_mappings = input("Vuoi creare mapping di test? (s/n): ")
            if create_mappings.lower() == 's':
                id_esercente_test = create_test_esercente_with_mappings(token)
    
    if not id_esercente_test:
        print("\n❌ Impossibile procedere senza un esercente con mapping")
        return
    
    # 4. Recupera i mapping dell'esercente
    mappings_data = get_social_mappings(token, id_esercente_test)
    
    # 5. Avvia un crawl di test
    print("\n" + "=" * 60)
    print("🎯 TEST CRAWLING")
    print("=" * 60)
    
    platform_to_test = input("Quale platform testare? (instagram/facebook/googlemaps) [instagram]: ").strip()
    if not platform_to_test:
        platform_to_test = "instagram"
    
    crawl_result = trigger_crawl_test(token, platform_to_test)
    
    if not crawl_result:
        print("\n❌ Impossibile avviare il crawl")
        return
    
    job_id = crawl_result.get("job_id")
    
    # 6. Monitora lo stato del job
    print("\n⏳ Monitoraggio del job (potrebbe richiedere diversi minuti)...")
    print("   Nota: I job di Bright Data possono richiedere da pochi minuti a diverse ore")
    
    max_checks = 10
    for i in range(max_checks):
        time.sleep(10)
        status_result = check_job_status(token, job_id)
        status = status_result.get("status", "unknown")
        
        if status == "completed":
            print("\n✅ Job completato!")
            break
        elif status == "failed":
            print("\n❌ Job fallito!")
            break
        else:
            print(f"   Controllo {i+1}/{max_checks}: Status = {status}")
    
    # 7. Se completato, scarica i risultati
    if status == "completed":
        download_results(token, job_id)
    else:
        print(f"\n⚠️  Job non ancora completato (status: {status})")
        print("   Puoi controllare manualmente lo stato con:")
        print(f"   GET {BASE_URL}/api/brightdata/status/{job_id}")
        print("   E scaricare i risultati quando è completato con:")
        print(f"   GET {BASE_URL}/api/brightdata/results/{job_id}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETATO")
    print("=" * 60)
    
    # Riepilogo
    print("\n📝 RIEPILOGO:")
    print(f"   - Esercente ID: {id_esercente_test}")
    print(f"   - Platform testato: {platform_to_test}")
    print(f"   - Job ID: {job_id}")
    print(f"   - Status finale: {status}")
    print("\nPer verificare i dati nel database:")
    print(f"   sqlite3 /app/backend/lookatme.db \"SELECT * FROM brightdata_jobs WHERE job_id='{job_id}';\"")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrotto dall'utente")
    except Exception as e:
        print(f"\n❌ Errore durante il test: {e}")
        import traceback
        traceback.print_exc()
