#!/bin/bash

# Configuration
API_BASE="http://localhost"
API_KEY="your_secure_admin_key_here"

echo "--- TG Storage API CLI Test ---"

# 1. Check Stats
echo -e "\n[1] Fetching Stats..."
curl -s -H "X-API-Key: $API_KEY" "$API_BASE/stats" | python3 -m json.tool

# 2. List Files
echo -e "\n[2] Listing Files..."
curl -s -H "X-API-Key: $API_KEY" "$API_BASE/files?limit=5" | python3 -m json.tool

# 3. Upload File (Example)
# echo "Hello TG" > test.txt
# echo -e "\n[3] Uploading test.txt..."
# curl -s -X POST -H "X-API-Key: $API_KEY" -F "file=@test.txt" "$API_BASE/upload" | python3 -m json.tool
