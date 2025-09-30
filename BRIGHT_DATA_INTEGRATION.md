# Bright Data Integration - Documentazione Completa

## Overview
L'integrazione con Bright Data permette di raccogliere automaticamente dati da:
- **Instagram**: followers, posts count
- **Facebook**: fans, reviews con rating  
- **Google Maps**: reviews count, rating

## Setup Completato

### Database
- ✅ PostgreSQL configurato e connesso
- ✅ Nuove tabelle create per Bright Data:
  - `brightdata_jobs`: Traccia i job di crawling
  - `brightdata_results`: Memorizza i risultati
  - `esercenti_social_mapping`: Collega esercenti agli URL social
  - `weekly_crawl_schedule`: Gestisce crawl settimanali automatici

### API Token
- ✅ Token configurato in `.env`: `BRIGHTDATA_API_TOKEN=2a833260d04380b94fbde50dcb924b5f583c3b6138f138ef2bedf6e3396e2248`
- ✅ Dataset IDs configurati per Instagram, Facebook, Google Maps

### Scheduler Automatico
- ✅ Crawl settimanale automatico ogni lunedì alle 9:00
- ✅ Controllo job completati ogni ora
- ✅ Integrazione automatica con dati esercenti esistenti

## Endpoint API Disponibili

### 1. Authentication
```bash
# Ottenere token di accesso
POST /get-token
Body: {"email": "admin@example.com", "password": "admin"}
```

### 2. Gestione Esercenti (Esistenti)
```bash
# Lista esercenti
GET /esercenti

# Crea esercente  
POST /esercenti
Body: {
  "nome": "Nome Esercente",
  "contatto": "email@example.com",
  "pagina_web_fb": "https://facebook.com/...",
  "pagina_ig": "https://instagram.com/...",
  "google_recensioni": "https://maps.google.com/..."
}
```

### 3. Bright Data Integration

#### 3.1 Mappature Social
```bash
# Crea mappature tra esercente e URL social
POST /api/brightdata/social-mapping
Body: {
  "id_esercente": 1,
  "mappings": [
    {
      "platform": "instagram",
      "url": "https://www.instagram.com/account/",
      "params": {}
    },
    {
      "platform": "facebook",
      "url": "https://www.facebook.com/page/reviews/",
      "params": {"num_of_reviews": 50}
    },
    {
      "platform": "googlemaps", 
      "url": "https://www.google.com/maps/place/...",
      "params": {"days_limit": 30}
    }
  ]
}

# Visualizza mappature di un esercente
GET /api/brightdata/social-mapping/{id_esercente}
```

#### 3.2 Crawling Manuale
```bash
# Avvia crawl manuale
POST /api/brightdata/trigger
Body: {
  "platform": "instagram",  # o "facebook" o "googlemaps"
  "urls": ["https://www.instagram.com/account/"],
  "params": {}
}

# Controlla stato job
GET /api/brightdata/status/{job_id}

# Recupera risultati (con integrazione automatica)
GET /api/brightdata/results/{job_id}?auto_integrate=true
```

#### 3.3 Crawling Settimanale Automatico
```bash
# Avvia crawl settimanale manualmente
POST /api/brightdata/weekly-crawl

# Controlla stato crawl settimanale
GET /api/brightdata/weekly-crawl/status
```

## Parametri Specifici per Platform

### Instagram
- **Dati estratti**: followers_count, posts_count
- **Parametri**: Nessuno specifico

### Facebook  
- **Dati estratti**: fans_count, reviews_count, rating
- **Parametri**: 
  - `num_of_reviews`: Numero di recensioni da raccogliere (default: 20)

### Google Maps
- **Dati estratti**: reviews_count, rating  
- **Parametri**:
  - `days_limit`: Giorni di recensioni da raccogliere (default: 30)

## Integrazione Automatica

Il sistema integra automaticamente i dati crawlati con la tabella `dati_crawled` esistente:
- **Instagram** → aggiorna `n_followers_ig`
- **Facebook** → aggiorna `n_fan_facebook`  
- **Google Maps** → aggiorna `stelle_google`

## Esempi di Test

### Test Completo - Script Bash
```bash
#!/bin/bash

# 1. Ottenere token
TOKEN=$(curl -s -X POST "http://localhost:8000/get-token" \
-H "Content-Type: application/json" \
-d '{"email": "admin@example.com", "password": "admin"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

echo "Token ottenuto: $TOKEN"

# 2. Creare esercente
ESERCENTE=$(curl -s -X POST "http://localhost:8000/esercenti" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "nome": "Test Business", 
  "contatto": "test@business.com",
  "pagina_ig": "https://www.instagram.com/cats_of_world_/"
}')

echo "Esercente creato: $ESERCENTE"

# 3. Creare mappature social
curl -X POST "http://localhost:8000/api/brightdata/social-mapping" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "id_esercente": 1,
  "mappings": [
    {
      "platform": "instagram",
      "url": "https://www.instagram.com/cats_of_world_/",
      "params": {}
    }
  ]
}'

# 4. Avviare crawl
CRAWL_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/brightdata/trigger" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "platform": "instagram",
  "urls": ["https://www.instagram.com/cats_of_world_/"],
  "params": {}
}')

echo "Crawl avviato: $CRAWL_RESPONSE"

# 5. Estrarre job_id e controllare stato
JOB_ID=$(echo $CRAWL_RESPONSE | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
echo "Job ID: $JOB_ID"

sleep 5
curl -X GET "http://localhost:8000/api/brightdata/status/$JOB_ID" \
-H "Authorization: Bearer $TOKEN"
```

## Monitoraggio e Logs

### Server Logs
```bash
# Controllare logs del server
tail -f /app/server.log

# Controllare status servizi  
ps aux | grep uvicorn
```

### Database Queries
```sql
-- Controllare job in corso
SELECT * FROM brightdata_jobs ORDER BY created_at DESC LIMIT 10;

-- Controllare risultati
SELECT * FROM brightdata_results ORDER BY extracted_at DESC LIMIT 10;

-- Controllare mappature
SELECT * FROM esercenti_social_mapping;

-- Controllare schedule settimanale
SELECT * FROM weekly_crawl_schedule ORDER BY week_start DESC;
```

## Risoluzione Problemi

### 1. Token Expired
- Sintomo: `{"detail":"Not authenticated"}`
- Soluzione: Richiedere nuovo token con `/get-token`

### 2. Job Non Trovato  
- Sintomo: `{"detail":"Job non trovato"}`
- Controllare: `SELECT * FROM brightdata_jobs WHERE job_id = 'xxx'`

### 3. API Bright Data Non Risponde
- Controllare: Token API valido
- Controllare: Parametri URL corretti
- Logs: Verificare `/app/server.log`

## Prossimi Passi

1. **Testing**: Testare tutti gli endpoint con dati reali
2. **Monitoring**: Implementare dashboard per monitorare crawl
3. **Ottimizzazione**: Aggiustare frequenza e parametri crawl
4. **Scaling**: Aggiungere più dataset se necessario

## Note Importanti

- ⚠️ Il token Bright Data deve rimanere valido e attivo
- ⚠️ I crawl settimanali partono automaticamente ogni lunedì alle 9:00
- ⚠️ I risultati vengono integrati automaticamente con i dati esistenti
- ⚠️ Verificare sempre i logs per eventuali errori di integrazione