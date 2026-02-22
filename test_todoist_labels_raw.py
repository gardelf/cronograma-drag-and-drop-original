#!/usr/bin/env python3
"""
Script para probar la API de Todoist directamente y ver las etiquetas raw
"""

import requests
import json

TODOIST_TOKEN = "50ff91ef15761a6727b8b991ac3be61a96f76538"

print("="*80)
print("🔍 PRUEBA DIRECTA DE LA API DE TODOIST - ETIQUETAS RAW")
print("="*80)

# Hacer llamada directa a la API
url = "https://api.todoist.com/rest/v1/tasks"
headers = {
    "Authorization": f"Bearer {TODOIST_TOKEN}"
}

print("\n1️⃣ Llamando a la API v2...")
response = requests.get(url, headers=headers)

print(f"   Status code: {response.status_code}")

if response.status_code == 200:
    tasks = response.json()
    print(f"   ✅ Total de tareas: {len(tasks)}")
    
    # Buscar tareas con "check" en el contenido o etiquetas
    print("\n2️⃣ Buscando tareas con 'check' en el contenido...")
    
    check_related_tasks = []
    for task in tasks:
        content = task.get('content', '').lower()
        labels = task.get('labels', [])
        
        # Buscar por contenido o etiquetas
        if 'check' in content or any('check' in str(label).lower() for label in labels):
            check_related_tasks.append(task)
    
    print(f"\n   📊 Encontradas {len(check_related_tasks)} tareas relacionadas con 'check'\n")
    
    if check_related_tasks:
        for i, task in enumerate(check_related_tasks[:10], 1):  # Mostrar solo las primeras 10
            print(f"\n   {i}. {task.get('content')}")
            print(f"      ID: {task.get('id')}")
            print(f"      Labels RAW: {task.get('labels')}")
            print(f"      Labels type: {type(task.get('labels'))}")
            if task.get('labels'):
                print(f"      Labels count: {len(task.get('labels'))}")
                for label in task.get('labels'):
                    print(f"         - '{label}' (type: {type(label)})")
    
    # Mostrar también una tarea completa raw
    print("\n" + "="*80)
    print("3️⃣ EJEMPLO DE TAREA RAW COMPLETA (primera tarea)")
    print("="*80)
    if tasks:
        print(json.dumps(tasks[0], indent=2, ensure_ascii=False))
    
else:
    print(f"   ❌ Error: {response.text}")

print("\n" + "="*80)
print("✅ Prueba completada")
print("="*80)
