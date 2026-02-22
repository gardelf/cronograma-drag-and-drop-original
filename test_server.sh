#!/bin/bash

echo "================================"
echo "🧪 Testing Web Server Endpoints"
echo "================================"
echo ""

echo "1️⃣ Testing /health endpoint..."
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""
echo ""

echo "2️⃣ Testing /cronograma endpoint (HTML)..."
response=$(curl -s -w "\n%{http_code}" http://localhost:8000/cronograma)
http_code=$(echo "$response" | tail -1)
content_length=$(echo "$response" | head -n -1 | wc -c)

if [ "$http_code" = "200" ]; then
    echo "✅ Status: $http_code OK"
    echo "✅ Content length: $content_length bytes"
    echo "✅ HTML content served successfully"
else
    echo "❌ Status: $http_code"
fi
echo ""
echo ""

echo "3️⃣ Testing /new-events endpoint..."
curl -s http://localhost:8000/new-events | python3 -m json.tool
echo ""
echo ""

echo "================================"
echo "✅ All endpoints tested"
echo "================================"
echo ""
echo "📋 To view the cronograma, open in your browser:"
echo "   http://localhost:8000"
echo ""
echo "🔧 Server logs:"
echo "   tail -f /home/ubuntu/daily-agenda-automation/web_server.log"
echo ""
