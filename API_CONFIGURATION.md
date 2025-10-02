# 🔑 Configurazione API Keys - Look At Me

Questa guida ti aiuterà a configurare tutte le chiavi API necessarie per il funzionamento completo dell'applicazione.

## 📋 Indice

1. [Setup Iniziale](#setup-iniziale)
2. [TripAdvisor API](#tripadvisor-api)
3. [Bright Data API](#bright-data-api)
4. [Verifica Configurazione](#verifica-configurazione)
5. [Troubleshooting](#troubleshooting)

---

## 🚀 Setup Iniziale

### Passo 1: Crea il file .env

Il file `.env` contiene tutte le chiavi API. È già stato creato in `/app/.env`.

### Passo 2: Modifica il file .env

Apri il file `/app/.env` e inserisci le tue chiavi API nei campi appropriati:

```bash
# Apri il file con un editor
nano /app/.env
# oppure
vim /app/.env
```

---

## 🏨 TripAdvisor API

### Come Ottenere la Chiave API

1. **Vai al TripAdvisor Developer Portal**
   - URL: https://www.tripadvisor.com/developers
   
2. **Registrati o Accedi**
   - Crea un account sviluppatore se non ne hai uno
   
3. **Crea una Nuova Applicazione**
   - Vai su "My Apps" > "Create a New App"
   - Compila i dettagli dell'applicazione
   - Seleziona le API necessarie:
     - Location API
     - Reviews API
   
4. **Ottieni la Chiave API**
   - Una volta creata l'app, copia la tua API Key
   - Incollala nel file `.env`:
   
   ```bash
   TRIPADVISOR_API_KEY=la_tua_chiave_api_qui
   ```

### Documentazione TripAdvisor

- Content API: https://www.tripadvisor.com/developers/content-api
- Rate Limits: Controlla i limiti nel tuo account developer

---

## 🌐 Bright Data API

### Come Ottenere il Token API

1. **Vai su Bright Data**
   - URL: https://brightdata.com/
   
2. **Accedi al tuo Account**
   - Se non hai un account, registrati
   
3. **Ottieni il Token API**
   - Dashboard > Account Settings > API Token
   - Copia il token
   
4. **Configura nel file .env**
   
   ```bash
   BRIGHTDATA_API_TOKEN=il_tuo_token_qui
   ```

### Dataset IDs

I dataset IDs sono già configurati nel file `.env`:

```bash
BRIGHTDATA_INSTAGRAM_DATASET=gd_l1vikfch901nx3by4
BRIGHTDATA_FACEBOOK_DATASET=gd_m0dtqpiu1mbcyc2g86
BRIGHTDATA_GOOGLEMAPS_DATASET=gd_luzfs1dn2oa0teb81
```

**Nota**: Questi sono i dataset IDs specifici per il tuo account. Se hai dataset diversi, aggiornali con i tuoi IDs dalla dashboard di Bright Data.

### Documentazione Bright Data

- API Docs: https://docs.brightdata.com/
- Dataset Trigger API: https://docs.brightdata.com/scraping-automation/api-reference/trigger

---

## ✅ Verifica Configurazione

Dopo aver configurato le chiavi API, verifica che tutto funzioni correttamente.

### 1. Riavvia il Backend

```bash
cd /app
pkill -f "uvicorn main:app"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
```

### 2. Ottieni un Token di Autenticazione

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/get-token \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "admin"}' | \
  grep -o '"token":"[^"]*"' | cut -d'"' -f4)

echo "Token: $TOKEN"
```

### 3. Testa TripAdvisor API

```bash
curl -X GET "http://localhost:8000/api/tripadvisor/test?location_id=123456" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Risposta Attesa con API Key Configurata:**
```json
{
  "api_configured": true,
  "api_key_present": "✅",
  ...
}
```

### 4. Testa Bright Data API

Crea un social mapping di test:

```bash
curl -X POST "http://localhost:8000/api/brightdata/social-mapping" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "id_esercente": 1,
    "platform": "instagram",
    "url": "https://instagram.com/test"
  }'
```

Poi trigger un crawl:

```bash
curl -X POST "http://localhost:8000/api/brightdata/trigger" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "instagram",
    "urls": ["https://instagram.com/test"]
  }' | python3 -m json.tool
```

**Risposta Attesa con Token Valido:**
```json
{
  "job_id": "s_xxxxxx",
  "status": "triggered",
  "message": "Crawl started successfully"
}
```

---

## 🔧 Troubleshooting

### Errore: "Unauthorized" (401)

**TripAdvisor:**
- Verifica che la chiave API sia corretta
- Controlla che l'API key non sia scaduta
- Verifica i rate limits nel dashboard TripAdvisor

**Bright Data:**
- Verifica che il token API sia valido
- Controlla il credito disponibile nel tuo account Bright Data
- Verifica che i dataset IDs siano corretti

### Errore: "API key not configured"

```bash
# Verifica che il file .env esista
ls -la /app/.env

# Verifica il contenuto
cat /app/.env | grep -E "TRIPADVISOR|BRIGHTDATA"

# Riavvia il backend
cd /app && pkill -f "uvicorn main:app"
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
```

### Il Backend Non Legge il File .env

```bash
# Verifica che python-dotenv sia installato
pip list | grep python-dotenv

# Se manca, installalo
pip install python-dotenv

# Verifica i log del backend
tail -f /tmp/backend.log
```

### Rate Limits Superati

**TripAdvisor:**
- Le API TripAdvisor hanno limiti di richieste
- Controlla il tuo piano nel dashboard developer
- Implementa un rate limiting se necessario

**Bright Data:**
- Bright Data ha limiti basati sul credito disponibile
- Monitora l'utilizzo nel dashboard
- Configura parametri di crawl appropriati (num_of_reviews, days_limit)

---

## 📊 Monitoraggio

### Controlla i Log

```bash
# Log backend completo
tail -f /tmp/backend.log

# Solo errori API
tail -f /tmp/backend.log | grep -i "error\|warning"

# Log scheduler settimanale
tail -f /tmp/backend.log | grep -i "scheduler\|weekly"
```

### Database Query

```bash
# Verifica job Bright Data
sqlite3 /app/lookatme.db "SELECT * FROM brightdata_jobs ORDER BY id DESC LIMIT 5;"

# Verifica dati crawlati
sqlite3 /app/lookatme.db "SELECT * FROM dati_crawled ORDER BY id DESC LIMIT 5;"
```

---

## 🔒 Sicurezza

### ⚠️ IMPORTANTE

1. **NON committare il file .env su Git**
   ```bash
   # Aggiungi al .gitignore
   echo ".env" >> /app/.gitignore
   ```

2. **Usa .env.example per il repository**
   - Il file `.env.example` contiene un template senza chiavi reali
   - Condividi solo questo file nel repository

3. **Cambia JWT_SECRET in produzione**
   ```bash
   # Genera una stringa casuale sicura
   JWT_SECRET=$(openssl rand -hex 32)
   ```

4. **Ruota le chiavi API periodicamente**
   - TripAdvisor: ogni 6-12 mesi
   - Bright Data: secondo le policy aziendali

---

## 📞 Supporto

Se hai problemi con la configurazione:

1. Controlla i log: `tail -f /tmp/backend.log`
2. Verifica la documentazione ufficiale delle API
3. Testa gli endpoint usando Swagger UI: http://localhost:8000/docs

---

## 🎯 Checklist Finale

- [ ] File .env creato in `/app/.env`
- [ ] TripAdvisor API key inserita
- [ ] Bright Data token inserito
- [ ] Dataset IDs verificati
- [ ] Backend riavviato
- [ ] Test TripAdvisor eseguito con successo
- [ ] Test Bright Data eseguito con successo
- [ ] File .env aggiunto a .gitignore
- [ ] JWT_SECRET cambiato (se in produzione)

**Configurazione completata! 🎉**
