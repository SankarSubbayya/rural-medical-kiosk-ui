#!/bin/bash
# Create consultation
CONSULT=$(curl -s -X POST http://localhost:8000/consultation/create \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "test-user", "language": "en"}')

CONSULT_ID=$(echo "$CONSULT" | jq -r '.consultation_id')
echo "=== Created consultation: $CONSULT_ID ==="
echo

# Message 1: White spots
echo "=== Message 1: White spots ==="
MSG1=$(curl -s -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d "{\"consultation_id\": \"$CONSULT_ID\", \"message\": \"I have white spots on my face above my eyebrows\", \"language\": \"en\"}")
echo "$MSG1" | jq -r '.message'
echo

# Message 2: Follow-up
echo "=== Message 2: They are getting bigger ==="
MSG2=$(curl -s -X POST http://localhost:8000/chat/message \
  -H "Content-Type: application/json" \
  -d "{\"consultation_id\": \"$CONSULT_ID\", \"message\": \"They are getting bigger\", \"language\": \"en\"}")
echo "$MSG2" | jq -r '.message'
echo

# Check history
echo "=== Conversation History ==="
curl -s "http://localhost:8000/chat/$CONSULT_ID/history" | jq '.messages[] | "\(.role): \(.content)"'
