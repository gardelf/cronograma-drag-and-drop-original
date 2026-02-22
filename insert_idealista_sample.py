#!/usr/bin/env python3
"""
Script to insert sample Idealista data into PostgreSQL database
"""
import os
import sys
import json
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from idealista_postgres import save_idealista_data

# Sample Idealista data
sample_data = {
    "properties": [
        {
            "propertyId": "123456789",
            "address": "Calle Pedro Zerolo, 28",
            "visitas": 145,
            "favoritos": 12,
            "mensajes": 8,
            "changes": {
                "visitas": 15,
                "favoritos": 2,
                "mensajes": 1
            }
        },
        {
            "propertyId": "987654321",
            "address": "Plaza de Rivas, 15",
            "visitas": 89,
            "favoritos": 7,
            "mensajes": 3,
            "changes": {
                "visitas": 8,
                "favoritos": 1,
                "mensajes": 0
            }
        }
    ],
    "timestamp": datetime.now().isoformat(),
    "last_updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}

print("📊 Insertando datos de ejemplo de Idealista...")
print(f"📊 Datos: {json.dumps(sample_data, indent=2, ensure_ascii=False)}")

try:
    save_idealista_data(sample_data)
    print("✅ Datos de ejemplo insertados correctamente")
except Exception as e:
    print(f"❌ Error insertando datos: {e}")
    import traceback
    traceback.print_exc()
