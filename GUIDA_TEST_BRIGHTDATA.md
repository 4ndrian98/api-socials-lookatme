# 🧪 Guida al Test di BrightData in Locale

Questa guida ti spiega come testare localmente se BrightData funziona correttamente, 
prelevando i link social dal database degli esercenti e scaricando i CSV.

## 📋 Prerequisiti

✅ Il backend deve essere attivo (già configurato)
✅ Token BrightData configurato nel file `.env`
✅ Database SQLite in `/app/backend/lookatme.db`

## 🚀 Metodo 1: Script Automatico (Consigliato)

Esegui lo script Python interattivo:

```bash
cd /app
python3 test_brightdata_local.py
```

Lo script farà automaticamente:
1. ✅ Autenticazione con il sistema
2. ✅ Lista gli esercenti esistenti nel database
3. ✅ Mostra i mapping social (link Instagram, Facebook, Google Maps)
4. ✅ Avvia un crawling di test su BrightData
5. ✅ Monitora lo stato del job
6. ✅ Scarica i risultati quando completato
7. ✅ Salva i risultati in formato JSON

### Output Atteso:

```
🧪 TEST BRIGHT DATA INTEGRATION
============================================================
🔐 Ottenendo token di autenticazione...
✅ Token ottenuto con successo

📋 Recuperando lista esercenti...
✅ Trovati 2 esercenti
   - ID: 1, Nome: My Restaurant
   - ID: 2, Nome: Test Restaurant BrightData

🔗 Recuperando mapping social per esercente ID 1...
✅ Trovati 3 mapping:
   - Platform: instagram, URL: https://www.instagram.com/myrestaurant
   - Platform: facebook, URL: https://www.facebook.com/myrestaurant
   - Platform: googlemaps, URL: https://www.google.com/maps/place/...

🚀 Avviando crawl di test per instagram...
✅ Crawl avviato con successo!
   Job ID: s_xyz123abc
   Dataset: instagram
   URL Count: 1

📊 Controllando stato del job...
✅ Status: running

⬇️  Scaricando risultati del job...
✅ Risultati scaricati!
   Risultati trovati: 1
   Integrati: true
   💾 Risultati salvati in: brightdata_results_s_xyz123abc.json
```

## 🔧 Metodo 2: Test Manuale con API

### 1. Ottieni il Token di Autenticazione

```bash
curl -X POST http://localhost:8001/get-token \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin"}'
```

Risposta:
```json
{"token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
```

Salva il token in una variabile:
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 2. Lista gli Esercenti

```bash
curl -X GET http://localhost:8001/esercenti \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Verifica i Mapping Social di un Esercente

```bash
curl -X GET http://localhost:8001/api/brightdata/social-mapping/1 \
  -H "Authorization: Bearer $TOKEN"
```

Risposta:
```json
{
  "esercente_id": 1,
  "mappings": [
    {
      "id": 1,
      "platform": "instagram",
      "url": "https://www.instagram.com/myrestaurant",
      "params": {},
      "is_active": "true",
      "last_crawled": null
    },
    {
      "id": 2,
      "platform": "facebook",
      "url": "https://www.facebook.com/myrestaurant",
      "params": {"num_of_reviews": 50},
      "is_active": "true",
      "last_crawled": null
    }
  ]
}
```

### 4. Avvia un Crawl Manuale

```bash
curl -X POST http://localhost:8001/api/brightdata/trigger \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "instagram",
    "urls": ["https://www.instagram.com/italianfood"],
    "params": {}
  }'
```

Risposta:
```json
{
  "job_id": "s_mg6i7z6y17xi70g1ba",
  "message": "Crawl avviato con successo per instagram",
  "dataset_type": "instagram",
  "url_count": 1
}
```

### 5. Controlla lo Stato del Job

```bash
JOB_ID="s_mg6i7z6y17xi70g1ba"

curl -X GET http://localhost:8001/api/brightdata/status/$JOB_ID \
  -H "Authorization: Bearer $TOKEN"
```

Risposta:
```json
{
  "job_id": "s_mg6i7z6y17xi70g1ba",
  "status": "completed",
  "progress": {},
  "results_available": true
}
```

### 6. Scarica i Risultati (CSV/JSON)

```bash
curl -X GET "http://localhost:8001/api/brightdata/results/$JOB_ID?auto_integrate=true" \
  -H "Authorization: Bearer $TOKEN" \
  > results.json
```

I risultati verranno:
- ✅ Salvati nel file `results.json`
- ✅ Memorizzati nella tabella `brightdata_results` del database
- ✅ Integrati automaticamente nella tabella `dati_crawled` (se auto_integrate=true)

## 📊 Verifica nel Database

### Controllo Job nel Database

```bash
sqlite3 /app/backend/lookatme.db "SELECT * FROM brightdata_jobs ORDER BY created_at DESC LIMIT 5;"
```

### Controllo Risultati

```bash
sqlite3 /app/backend/lookatme.db "SELECT * FROM brightdata_results ORDER BY extracted_at DESC LIMIT 5;"
```

### Controllo Social Mappings

```bash
sqlite3 /app/backend/lookatme.db "SELECT * FROM esercenti_social_mapping WHERE is_active='true';"
```

### Controllo Dati Integrati

```bash
sqlite3 /app/backend/lookatme.db "SELECT id_esercente, data, n_followers_ig, n_fan_facebook, stelle_google FROM dati_crawled ORDER BY data DESC LIMIT 5;"
```

## 🔄 Crawl Settimanale Automatico

### Avvia Crawl Settimanale

```bash
curl -X POST http://localhost:8001/api/brightdata/weekly-crawl \
  -H "Authorization: Bearer $TOKEN"
```

Questo crawlerà automaticamente TUTTI gli esercenti che hanno mapping social attivi.

### Controlla lo Stato del Crawl Settimanale

```bash
curl -X GET http://localhost:8001/api/brightdata/weekly-crawl/status \
  -H "Authorization: Bearer $TOKEN"
```

## 📝 Formato Risultati CSV/JSON

### Esempio Risultato Instagram

```json
{
  "url": "https://www.instagram.com/italianfood",
  "followers": 125000,
  "following": 450,
  "posts": 890,
  "bio": "Authentic Italian Cuisine",
  "profile_picture": "https://...",
  "is_verified": true,
  "is_business": true
}
```

### Esempio Risultato Facebook

```json
{
  "url": "https://www.facebook.com/italianrestaurant",
  "fans": 45000,
  "rating": 4.5,
  "reviews": [
    {
      "text": "Great food!",
      "rating": 5,
      "date": "2025-01-15"
    }
  ]
}
```

### Esempio Risultato Google Maps

```json
{
  "url": "https://www.google.com/maps/place/...",
  "rating": 4.7,
  "reviews_count": 1250,
  "reviews": [
    {
      "author": "John Doe",
      "rating": 5,
      "text": "Excellent service!",
      "date": "2025-01-10"
    }
  ]
}
```

## ⚠️ Note Importanti

1. **Tempo di Elaborazione**: I job di BrightData possono richiedere da pochi minuti a diverse ore
2. **Rate Limiting**: BrightData ha limiti di richieste, non fare troppi test consecutivi
3. **Costi**: Ogni crawl consuma crediti BrightData
4. **Auto-Integration**: I dati vengono automaticamente integrati nella tabella `dati_crawled`

## 🐛 Troubleshooting

### Il backend non risponde

```bash
sudo supervisorctl status backend
sudo supervisorctl restart backend
tail -f /var/log/supervisor/backend.err.log
```

### Token BrightData non configurato

Verifica il file `/app/backend/.env`:
```bash
cat /app/backend/.env | grep BRIGHTDATA
```

### Database non trovato

```bash
ls -la /app/backend/lookatme.db
```

### Job rimane in status "triggered" per troppo tempo

È normale! BrightData può richiedere tempo. Controlla dopo qualche ora.

## 📞 Supporto

Per problemi con:
- **BrightData API**: Controlla la documentazione ufficiale o il dashboard BrightData
- **Backend/Database**: Controlla i log con `tail -f /var/log/supervisor/backend.err.log`
- **Script di test**: Esegui con `python3 -v test_brightdata_local.py` per output verbose

---

✅ **Pronto per testare!** Inizia con il Metodo 1 (Script Automatico) per un test completo.
