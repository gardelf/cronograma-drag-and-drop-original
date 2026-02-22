import requests
import os
from datetime import datetime

# Configuración
FIREFLY_URL = "https://firefly-core-production-f02a.up.railway.app"
FIREFLY_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiYWM4YTEyZTUyOWI4N2M3ZTAyNDRkYTc5MjNjMWM5MzgzMzMwNGQ2NGZjOTU0M2EyNTZiZmZiZTg2ZjJmMmM2ZjE0MTQ5MTkyNTU0OTQ2ZWEiLCJpYXQiOjE3NjUyMjA1NzEuNzc3Mzg3LCJuYmYiOjE3NjUyMjA1NzEuNzc3Mzg5LCJleHAiOjE3OTY3NTY1NzEuNzUzMDk2LCJzdWIiOiIxIiwic2NvcGVzIjpbXX0.dGVWqJVMd9Oe0i-6A6hTKZKqo3Yz-Ky0-5yNWqwJH4Aq_Yj4Z-0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQqJZ0Yq4wMQ"

# Consultar transacciones de noviembre 2025
start_date = "2025-11-01"
end_date = "2025-11-30"

url = f"{FIREFLY_URL}/api/v1/transactions"
headers = {
    "Authorization": f"Bearer {FIREFLY_TOKEN}",
    "Accept": "application/json"
}
params = {
    "start": start_date,
    "end": end_date,
    "type": "withdrawal"
}

print(f"🔍 Consultando transacciones de noviembre 2025...")
print(f"   URL: {url}")
print(f"   Fechas: {start_date} a {end_date}")

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    transactions = data.get('data', [])
    
    print(f"\n✅ Respuesta exitosa")
    print(f"   Total de transacciones: {len(transactions)}")
    
    total = 0.0
    print("\n📋 Transacciones de noviembre:")
    for trans in transactions:
        attrs = trans.get('attributes', {})
        trans_list = attrs.get('transactions', [])
        for t in trans_list:
            amount = float(t.get('amount', 0))
            description = t.get('description', 'Sin descripción')
            date = t.get('date', '')
            total += abs(amount)
            print(f"   • {date[:10]} - {description}: {abs(amount):.2f} EUR")
    
    print(f"\n💰 TOTAL GASTOS NOVIEMBRE: {total:.2f} EUR")
else:
    print(f"\n❌ Error: {response.status_code}")
    print(f"   {response.text}")
