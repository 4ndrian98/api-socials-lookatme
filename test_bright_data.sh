#!/bin/bash

# Test Script per Bright Data Integration
echo "🚀 Testing Bright Data Integration..."

BASE_URL="http://localhost:8000"

# Check if server is running
echo "📡 Checking server status..."
if ! curl -s $BASE_URL/docs > /dev/null; then
    echo "❌ Server not running! Start with: uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
    exit 1
fi
echo "✅ Server is running"

# 1. Get authentication token
echo "🔑 Getting authentication token..."
TOKEN=$(curl -s -X POST "$BASE_URL/get-token" \
-H "Content-Type: application/json" \
-d '{"email": "admin@example.com", "password": "admin"}' | grep -o '"token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get authentication token"
    exit 1
fi
echo "✅ Token obtained: ${TOKEN:0:20}..."

# 2. Create test esercente
echo "🏢 Creating test esercente..."
ESERCENTE_RESPONSE=$(curl -s -X POST "$BASE_URL/esercenti" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "nome": "Test Business - Bright Data",
  "contatto": "test@brightdata.com",
  "pagina_ig": "https://www.instagram.com/cats_of_world_/",
  "pagina_web_fb": "https://www.facebook.com/PepsiCo/reviews/",
  "google_recensioni": "https://maps.google.com/test"
}')

ESERCENTE_ID=$(echo $ESERCENTE_RESPONSE | grep -o '"id_esercente":[0-9]*' | cut -d':' -f2)
if [ -z "$ESERCENTE_ID" ]; then
    echo "❌ Failed to create esercente"
    echo "Response: $ESERCENTE_RESPONSE"
    exit 1
fi
echo "✅ Esercente created with ID: $ESERCENTE_ID"

# 3. Create social mappings
echo "📱 Creating social mappings..."
MAPPING_RESPONSE=$(curl -s -X POST "$BASE_URL/api/brightdata/social-mapping" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d "{
  \"id_esercente\": $ESERCENTE_ID,
  \"mappings\": [
    {
      \"platform\": \"instagram\",
      \"url\": \"https://www.instagram.com/cats_of_world_/\",
      \"params\": {}
    },
    {
      \"platform\": \"facebook\",
      \"url\": \"https://www.facebook.com/PepsiCo/reviews/\",
      \"params\": {\"num_of_reviews\": 20}
    }
  ]
}")

MAPPINGS_COUNT=$(echo $MAPPING_RESPONSE | grep -o '"mappings_created":[0-9]*' | cut -d':' -f2)
if [ "$MAPPINGS_COUNT" != "2" ]; then
    echo "❌ Failed to create social mappings"
    echo "Response: $MAPPING_RESPONSE"
    exit 1
fi
echo "✅ Created $MAPPINGS_COUNT social mappings"

# 4. Test manual crawl trigger
echo "🕷️ Triggering manual crawl..."
CRAWL_RESPONSE=$(curl -s -X POST "$BASE_URL/api/brightdata/trigger" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "platform": "instagram",
  "urls": ["https://www.instagram.com/cats_of_world_/"],
  "params": {}
}')

JOB_ID=$(echo $CRAWL_RESPONSE | grep -o '"job_id":"[^"]*"' | cut -d'"' -f4)
if [ -z "$JOB_ID" ]; then
    echo "❌ Failed to trigger crawl"
    echo "Response: $CRAWL_RESPONSE"
    exit 1
fi
echo "✅ Crawl triggered with Job ID: $JOB_ID"

# 5. Check job status
echo "📊 Checking job status..."
sleep 2
STATUS_RESPONSE=$(curl -s -X GET "$BASE_URL/api/brightdata/status/$JOB_ID" \
-H "Authorization: Bearer $TOKEN")

JOB_STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
echo "✅ Job status: $JOB_STATUS"

# 6. Check social mappings
echo "🔍 Retrieving social mappings..."
RETRIEVE_RESPONSE=$(curl -s -X GET "$BASE_URL/api/brightdata/social-mapping/$ESERCENTE_ID" \
-H "Authorization: Bearer $TOKEN")

MAPPING_COUNT=$(echo $RETRIEVE_RESPONSE | grep -o '"platform"' | wc -l)
echo "✅ Found $MAPPING_COUNT social mappings for esercente"

# 7. Test weekly crawl status
echo "📅 Checking weekly crawl status..."
WEEKLY_STATUS=$(curl -s -X GET "$BASE_URL/api/brightdata/weekly-crawl/status" \
-H "Authorization: Bearer $TOKEN")
echo "✅ Weekly crawl status retrieved"

# 8. Check database tables
echo "📀 Checking database tables..."
python3 -c "
from database import SessionLocal
from models import BrightDataJob, BrightDataResult, EsercenteSocialMapping, WeeklyCrawlSchedule, Esercente

db = SessionLocal()
try:
    jobs_count = db.query(BrightDataJob).count()
    mappings_count = db.query(EsercenteSocialMapping).count()
    esercenti_count = db.query(Esercente).count()
    
    print(f'✅ Database tables:')
    print(f'   - Esercenti: {esercenti_count}')
    print(f'   - BrightData Jobs: {jobs_count}')
    print(f'   - Social Mappings: {mappings_count}')
    
    if jobs_count > 0:
        latest_job = db.query(BrightDataJob).order_by(BrightDataJob.created_at.desc()).first()
        print(f'   - Latest Job: {latest_job.job_id} ({latest_job.status})')
    
finally:
    db.close()
"

echo "🎉 All tests completed successfully!"
echo ""
echo "📚 Next steps:"
echo "   1. Check server logs: tail -f /app/server.log"
echo "   2. Monitor job progress in database"
echo "   3. Wait for job completion (can take several minutes)"
echo "   4. Use GET /api/brightdata/results/{job_id} to retrieve results"
echo "   5. Check integration with existing esercenti data"
echo ""
echo "🔗 API Documentation: http://localhost:8000/docs"
echo "📊 Created Esercente ID: $ESERCENTE_ID"
echo "🆔 Test Job ID: $JOB_ID"