#!/bin/bash

# Script per verificare la configurazione delle API keys

echo "🔍 Controllo Configurazione API Keys"
echo "======================================"
echo ""

# Controlla se il file .env esiste
if [ ! -f "/app/.env" ]; then
    echo "❌ File .env non trovato in /app/.env"
    echo "   Crea il file copiando .env.example:"
    echo "   cp /app/.env.example /app/.env"
    exit 1
fi

echo "✅ File .env trovato"
echo ""

# Carica le variabili dal file .env
source /app/.env 2>/dev/null

echo "📋 Stato Configurazione:"
echo "------------------------"

# TripAdvisor
echo -n "TripAdvisor API Key: "
if [ -z "$TRIPADVISOR_API_KEY" ]; then
    echo "❌ NON CONFIGURATA"
    echo "   Aggiungi: TRIPADVISOR_API_KEY=tua_chiave nel file .env"
else
    # Mostra solo i primi e ultimi 4 caratteri
    KEY_LEN=${#TRIPADVISOR_API_KEY}
    if [ $KEY_LEN -gt 8 ]; then
        MASKED="${TRIPADVISOR_API_KEY:0:4}...${TRIPADVISOR_API_KEY: -4}"
        echo "✅ CONFIGURATA ($MASKED)"
    else
        echo "⚠️  CONFIGURATA ma sembra troppo corta"
    fi
fi

# Bright Data Token
echo -n "Bright Data Token: "
if [ -z "$BRIGHTDATA_API_TOKEN" ]; then
    echo "❌ NON CONFIGURATO"
    echo "   Aggiungi: BRIGHTDATA_API_TOKEN=tuo_token nel file .env"
else
    TOKEN_LEN=${#BRIGHTDATA_API_TOKEN}
    if [ $TOKEN_LEN -gt 8 ]; then
        MASKED="${BRIGHTDATA_API_TOKEN:0:4}...${BRIGHTDATA_API_TOKEN: -4}"
        echo "✅ CONFIGURATO ($MASKED)"
    else
        echo "⚠️  CONFIGURATO ma sembra troppo corto"
    fi
fi

# JWT Secret
echo -n "JWT Secret: "
if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" == "change-me-please" ] || [ "$JWT_SECRET" == "change-me-please-use-random-string-in-production" ]; then
    echo "⚠️  USANDO VALORE DI DEFAULT (cambialo in produzione!)"
else
    echo "✅ CONFIGURATO (personalizzato)"
fi

echo ""
echo "📊 Dataset IDs Bright Data:"
echo "---------------------------"
echo "Instagram: ${BRIGHTDATA_INSTAGRAM_DATASET:-❌ Non configurato}"
echo "Facebook: ${BRIGHTDATA_FACEBOOK_DATASET:-❌ Non configurato}"
echo "Google Maps: ${BRIGHTDATA_GOOGLEMAPS_DATASET:-❌ Non configurato}"

echo ""
echo "🧪 Test API Endpoints:"
echo "----------------------"

# Controlla se il backend è attivo
if ! curl -s http://localhost:8000/docs > /dev/null; then
    echo "❌ Backend non risponde su porta 8000"
    echo "   Avvia il backend con:"
    echo "   cd /app && nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &"
    exit 1
fi

echo "✅ Backend attivo su porta 8000"

# Ottieni token
TOKEN=$(curl -s -X POST http://localhost:8000/get-token \
    -H "Content-Type: application/json" \
    -d '{"email": "admin@example.com", "password": "admin"}' | \
    grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Impossibile ottenere token di autenticazione"
    exit 1
fi

echo "✅ Token di autenticazione ottenuto"

# Test TripAdvisor
echo ""
echo -n "Test TripAdvisor API: "
TRIPADVISOR_TEST=$(curl -s -X GET "http://localhost:8000/api/tripadvisor/test?location_id=123456" \
    -H "Authorization: Bearer $TOKEN")

API_KEY_PRESENT=$(echo $TRIPADVISOR_TEST | grep -o '"api_key_present":"[^"]*"' | cut -d'"' -f4)

if [ "$API_KEY_PRESENT" == "✅" ]; then
    echo "✅ API Key configurata e caricata"
else
    echo "❌ API Key non configurata o non caricata"
    echo "   Verifica il file .env e riavvia il backend"
fi

echo ""
echo "======================================"
echo "📖 Per maggiori informazioni, leggi:"
echo "   /app/API_CONFIGURATION.md"
echo ""
echo "🔄 Dopo aver modificato .env, riavvia il backend:"
echo "   cd /app && pkill -f 'uvicorn main:app'"
echo "   nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &"
echo ""
