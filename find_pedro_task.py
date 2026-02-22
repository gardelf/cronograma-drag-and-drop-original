#!/usr/bin/env python3
"""
Script para buscar la tarea específica de Pedro Zerolo
"""

from todoist_client import TodoistClient
import json

TODOIST_TOKEN = "50ff91ef15761a6727b8b991ac3be61a96f76538"

print("="*80)
print("🔍 BUSCANDO TAREA: Pedro Zerolo arquitecto fachada")
print("="*80)

# Inicializar cliente
client = TodoistClient(TODOIST_TOKEN)

# Obtener TODAS las tareas (sin filtrar por fecha)
print("\n1️⃣ Obteniendo TODAS las tareas activas (sin filtro de fecha)...")
all_tasks_raw = client.get_all_active_tasks()
print(f"   Total tareas RAW: {len(all_tasks_raw)}")

# Buscar la tarea de Pedro Zerolo en las tareas RAW
pedro_tasks_raw = [t for t in all_tasks_raw if 'Pedro' in t.get('content', '') or 'Zerolo' in t.get('content', '')]
print(f"\n2️⃣ Tareas con 'Pedro' o 'Zerolo' en RAW: {len(pedro_tasks_raw)}")

if pedro_tasks_raw:
    for task in pedro_tasks_raw:
        print(f"\n   Tarea encontrada (RAW):")
        print(f"   Content: {task.get('content')}")
        print(f"   Labels: {task.get('labels')}")
        print(f"   Due: {task.get('due')}")
        print(f"   Project ID: {task.get('project_id')}")
        print(f"   JSON completo:")
        print(json.dumps(task, indent=2, ensure_ascii=False))
else:
    print("   ⚠️ NO encontrada en tareas RAW")

# Ahora formatear y buscar
print("\n3️⃣ Formateando tareas...")
formatted_tasks = client.format_tasks_for_display(all_tasks_raw)
print(f"   Total tareas formateadas: {len(formatted_tasks)}")

pedro_tasks_formatted = [t for t in formatted_tasks if 'Pedro' in t.get('content', '') or 'Zerolo' in t.get('content', '')]
print(f"\n4️⃣ Tareas con 'Pedro' o 'Zerolo' en FORMATEADAS: {len(pedro_tasks_formatted)}")

if pedro_tasks_formatted:
    for task in pedro_tasks_formatted:
        print(f"\n   Tarea encontrada (FORMATEADA):")
        print(f"   Content: {task.get('content')}")
        print(f"   Labels: {task.get('labels')}")
        print(f"   Due date: {task.get('due_date')}")
        print(f"   Due time: {task.get('due_time')}")
        print(f"   Priority: {task.get('priority')}")
        print(f"   JSON completo:")
        print(json.dumps(task, indent=2, ensure_ascii=False))
else:
    print("   ⚠️ NO encontrada en tareas formateadas")

# Buscar tareas con etiqueta "check" en RAW
print("\n5️⃣ Buscando tareas con etiqueta 'check' en RAW...")
check_tasks = []
for task in all_tasks_raw:
    labels = task.get('labels', [])
    if any('check' in str(label).lower() for label in labels):
        check_tasks.append(task)

print(f"   Total tareas con 'check' en etiquetas: {len(check_tasks)}")
if check_tasks:
    for task in check_tasks[:3]:  # Mostrar solo las primeras 3
        print(f"\n   - {task.get('content')}")
        print(f"     Labels: {task.get('labels')}")

print("\n" + "="*80)
print("✅ Búsqueda completada")
print("="*80)
