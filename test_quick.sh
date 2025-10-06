#!/bin/bash
# Script di test rapido per BrightData

echo "=================================="
echo "🧪 TEST RAPIDO BRIGHTDATA"
echo "=================================="
echo ""

# 1. Ottieni token
echo "1️⃣  Ottenendo token..."
TOKEN=$(curl -s -X POST http://localhost:8001/get-token \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

if [ -z "$TOKEN" ]; then
    echo "❌ Errore nell'ottenere il token"
    exit 1
fi
echo "✅ Token ottenuto"
echo ""

# 2. Lista esercenti
echo "2️⃣  Lista esercenti con mapping social:"
echo ""
cd /app/backend && sqlite3 lookatme.db "
SELECT 
    e.id_esercente, 
    e.nome,
    GROUP_CONCAT(m.platform || ': ' || m.url, '\n       ') as mappings
FROM esercenti e
LEFT JOIN esercenti_social_mapping m ON e.id_esercente = m.id_esercente
WHERE m.id IS NOT NULL
GROUP BY e.id_esercente
LIMIT 5;
" | while IFS='|' read -r id nome mappings; do
    echo "   📍 ID: $id - $nome"
    echo "      Social: $mappings"
    echo ""
done

# 3. Mostra come triggare un crawl
echo "3️⃣  Per avviare un crawl manuale:"
echo ""
echo "   curl -X POST http://localhost:8001/api/brightdata/trigger \\"
echo "     -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{
      \"platform\": \"instagram\",
      \"urls\": [\"https://www.instagram.com/cats_of_world_/\"],
      \"params\": {}
    }'"
echo ""

# 4. Mostra job esistenti
echo "4️⃣  Job BrightData nel database:"
cd /app/backend && sqlite3 lookatme.db "
SELECT 
    job_id,
    dataset_type,
    status,
    created_at
FROM brightdata_jobs
ORDER BY created_at DESC
LIMIT 5;
" | while IFS='|' read -r job_id dataset status created; do
    echo "   🔄 Job: $job_id"
    echo "      Platform: $dataset | Status: $status | Created: $created"
    echo ""
done

if [ $? -ne 0 ]; then
    echo "   ℹ️  Nessun job trovato (tabella potrebbe non esistere ancora)"
    echo ""
fi

# 5. Istruzioni
echo "=================================="
echo "📚 PROSSIMI PASSI:"
echo "=================================="
echo ""
echo "✅ Backend attivo su: http://localhost:8001"
echo "✅ Database: /app/backend/lookatme.db"
echo "✅ Token BrightData configurato"
echo ""
echo "Per test completo interattivo:"
echo "   python3 /app/test_brightdata_local.py"
echo ""
echo "Per documentazione completa:"
echo "   cat /app/GUIDA_TEST_BRIGHTDATA.md"
echo ""
echo "Per verificare mappings di un esercente (es. ID=4):"
echo "   curl -X GET http://localhost:8001/api/brightdata/social-mapping/4 \\"
echo "     -H \"Authorization: Bearer $TOKEN\" | python3 -m json.tool"
echo ""
