#!/bin/bash
# Railway initialization script

echo "🚀 Inicializando sistema de cronograma automatizado..."

# Remove any .env file to ensure Railway environment variables are used
if [ -f ".env" ]; then
    echo "🗑️  Eliminando archivo .env local para usar variables de Railway..."
    rm -f .env
fi

# Create database if it doesn't exist
if [ ! -f "events_tracker.db" ]; then
    echo "📊 Creando base de datos..."
    python3.11 -c "from events_db import init_db; init_db()"
fi

# Generate initial cronograma
echo "📅 Generando cronograma inicial..."
python3.11 cronograma_generator_v7_5.py || echo "⚠️  Advertencia: No se pudo generar cronograma inicial (se generará en la primera petición)"

echo "✅ Inicialización completada"
echo "🌐 Iniciando servidor web (incluye API de gastos)..."

# Start web server (includes expense API endpoints)
python3.11 web_server.py
