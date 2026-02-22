#!/usr/bin/env python3.11
"""
Script de diagnóstico para verificar la conexión con Todoist API
y la configuración de variables de entorno en Railway
"""

import os
import sys
from config import get_config, load_env_file
from todoist_client import TodoistClient
import requests

print("="*80)
print("🔍 DIAGNÓSTICO DE CONEXIÓN CON TODOIST")
print("="*80)

# 1. Verificar variables de entorno
print("\n1️⃣ Verificando variables de entorno...")
load_env_file()

config = get_config()
todoist_token = config.get('TODOIST_API_TOKEN', '')

print(f"   TODOIST_API_TOKEN existe: {bool(todoist_token)}")
print(f"   TODOIST_API_TOKEN longitud: {len(todoist_token)}")
if todoist_token:
    print(f"   TODOIST_API_TOKEN primeros 10 caracteres: {todoist_token[:10]}...")
    print(f"   TODOIST_API_TOKEN últimos 10 caracteres: ...{todoist_token[-10:]}")
else:
    print("   ❌ ERROR: TODOIST_API_TOKEN no está configurado")
    sys.exit(1)

# 2. Verificar conexión directa con API de Todoist
print("\n2️⃣ Probando conexión directa con API de Todoist...")
try:
    url = "https://api.todoist.com/rest/v1/tasks"
    headers = {
        "Authorization": f"Bearer {todoist_token}",
        "Content-Type": "application/json"
    }
    
    print(f"   URL: {url}")
    print(f"   Headers: Authorization: Bearer {todoist_token[:10]}...")
    
    response = requests.get(url, headers=headers, timeout=10)
    
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        tasks = response.json()
        print(f"   ✅ Conexión exitosa!")
        print(f"   Total de tareas activas: {len(tasks)}")
        
        if len(tasks) > 0:
            print(f"\n   Primeras 5 tareas:")
            for i, task in enumerate(tasks[:5], 1):
                content = task.get('content', 'Sin título')
                priority = task.get('priority', 1)
                due = task.get('due', {})
                due_date = due.get('date', 'Sin fecha') if due else 'Sin fecha'
                print(f"      {i}. {content} (Prioridad: {priority}, Fecha: {due_date})")
        else:
            print("   ⚠️  No hay tareas activas en Todoist")
    
    elif response.status_code == 401:
        print(f"   ❌ ERROR 401: Token inválido o expirado")
        print(f"   Respuesta: {response.text}")
    
    elif response.status_code == 403:
        print(f"   ❌ ERROR 403: Acceso prohibido")
        print(f"   Respuesta: {response.text}")
    
    else:
        print(f"   ❌ ERROR {response.status_code}")
        print(f"   Respuesta: {response.text}")

except requests.exceptions.Timeout:
    print("   ❌ ERROR: Timeout al conectar con Todoist API")
except requests.exceptions.ConnectionError:
    print("   ❌ ERROR: No se pudo conectar con Todoist API")
except Exception as e:
    print(f"   ❌ ERROR inesperado: {e}")
    import traceback
    traceback.print_exc()

# 3. Verificar usando TodoistClient
print("\n3️⃣ Probando con TodoistClient...")
try:
    client = TodoistClient(todoist_token)
    
    print("   Obteniendo todas las tareas activas...")
    all_tasks = client.get_all_active_tasks()
    print(f"   ✅ Total de tareas obtenidas: {len(all_tasks)}")
    
    print("\n   Formateando tareas...")
    formatted_tasks = client.format_tasks_for_display(all_tasks)
    print(f"   ✅ Tareas formateadas: {len(formatted_tasks)}")
    
    if len(formatted_tasks) > 0:
        print(f"\n   Detalles de las primeras 3 tareas formateadas:")
        for i, task in enumerate(formatted_tasks[:3], 1):
            print(f"\n      Tarea {i}:")
            print(f"         ID: {task.get('id')}")
            print(f"         Contenido: {task.get('content')}")
            print(f"         Prioridad: {task.get('priority')} (valor: {task.get('priority_value')})")
            print(f"         Fecha: {task.get('due_date')}")
            print(f"         Hora: {task.get('due_time')}")
            print(f"         Etiquetas: {task.get('labels')}")
    
    # Filtrar tareas para hoy
    from datetime import datetime
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    today_tasks = []
    for task in formatted_tasks:
        due_date = task.get('due_date')
        if due_date is None or due_date <= today_str:
            today_tasks.append(task)
    
    print(f"\n   Tareas para hoy o sin fecha: {len(today_tasks)}")
    
except Exception as e:
    print(f"   ❌ ERROR con TodoistClient: {e}")
    import traceback
    traceback.print_exc()

# 4. Verificar otras variables de entorno relevantes
print("\n4️⃣ Verificando otras variables de entorno...")
print(f"   ICLOUD_USERNAME: {config.get('ICLOUD_USERNAME', 'NO CONFIGURADO')}")
print(f"   ICLOUD_APP_PASSWORD existe: {bool(config.get('ICLOUD_APP_PASSWORD'))}")
print(f"   OPENAI_API_KEY existe: {bool(config.get('OPENAI_API_KEY'))}")
print(f"   PORT: {config.get('PORT', 'NO CONFIGURADO')}")

print("\n" + "="*80)
print("✅ DIAGNÓSTICO COMPLETADO")
print("="*80)
