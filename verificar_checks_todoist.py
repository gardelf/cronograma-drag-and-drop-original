#!/usr/bin/env python3
"""
Script para verificar las tareas con etiquetas "checks" en Todoist
"""

from todoist_client import TodoistClient
from datetime import datetime
import json

# Token de Todoist
TODOIST_TOKEN = "50ff91ef15761a6727b8b991ac3be61a96f76538"

print("="*80)
print("🔍 VERIFICACIÓN DE TAREAS CON ETIQUETA 'CHECKS' EN TODOIST")
print("="*80)

# Inicializar cliente
client = TodoistClient(TODOIST_TOKEN)

# Obtener todas las tareas activas
print("\n1️⃣ Obteniendo todas las tareas activas...")
all_tasks = client.get_all_active_tasks()
print(f"   ✅ Total de tareas activas: {len(all_tasks)}")

# Formatear tareas
formatted_tasks = client.format_tasks_for_display(all_tasks)

# Filtrar tareas para hoy
today_str = datetime.now().strftime("%Y-%m-%d")
today_tasks = []
for task in formatted_tasks:
    due_date = task.get('due_date')
    if due_date is None or due_date <= today_str:
        today_tasks.append(task)

print(f"   ✅ Tareas para hoy o sin fecha: {len(today_tasks)}")

# Función para detectar checks
def has_checks_label(task):
    """Check if task has any variant of the 'checks' label"""
    labels = task.get("labels", [])
    labels_lower = [l.lower() for l in labels]
    checks_variants = ["checks", "check", "cheks", "chek"]
    return any(variant in labels_lower for variant in checks_variants)

# Buscar tareas con etiqueta checks
print("\n2️⃣ Buscando tareas con etiquetas 'checks'...")
checks_tasks = [t for t in today_tasks if has_checks_label(t)]

print(f"\n   📊 RESULTADO: {len(checks_tasks)} tareas con etiqueta 'checks'\n")

if checks_tasks:
    print("   Tareas encontradas:")
    for i, task in enumerate(checks_tasks, 1):
        print(f"\n   {i}. {task['content']}")
        print(f"      ID: {task['id']}")
        print(f"      Prioridad: {task['priority']}")
        print(f"      Etiquetas: {task.get('labels', [])}")
        print(f"      Fecha: {task.get('due_date', 'Sin fecha')}")
        print(f"      Hora: {task.get('due_time', 'Sin hora')}")
else:
    print("   ⚠️ No se encontraron tareas con etiquetas 'checks'")
    print("\n   Mostrando todas las etiquetas únicas en las tareas de hoy:")
    all_labels = set()
    for task in today_tasks:
        all_labels.update(task.get('labels', []))
    
    if all_labels:
        for label in sorted(all_labels):
            print(f"      - {label}")
            # Contar cuántas tareas tienen esta etiqueta
            count = sum(1 for t in today_tasks if label in t.get('labels', []))
            print(f"        ({count} tareas)")
    else:
        print("      No hay etiquetas en ninguna tarea")

print("\n" + "="*80)
print("✅ Verificación completada")
print("="*80)
