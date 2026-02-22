#!/usr/bin/env python3
"""
Script para debuggear las etiquetas que llegan de Todoist
"""

from todoist_client import TodoistClient
from datetime import datetime

TODOIST_TOKEN = "50ff91ef15761a6727b8b991ac3be61a96f76538"

print("="*80)
print("🔍 DEBUG: ETIQUETAS DE TODOIST")
print("="*80)

# Inicializar cliente
client = TodoistClient(TODOIST_TOKEN)

# Obtener todas las tareas activas
print("\n1️⃣ Obteniendo tareas activas...")
all_tasks = client.get_all_active_tasks()
print(f"   Total tareas: {len(all_tasks)}")

# Formatear tareas
formatted_tasks = client.format_tasks_for_display(all_tasks)

# Filtrar tareas para hoy
today_str = datetime.now().strftime("%Y-%m-%d")
today_tasks = []
for task in formatted_tasks:
    due_date = task.get('due_date')
    if due_date is None or due_date <= today_str:
        today_tasks.append(task)

print(f"   Tareas para hoy: {len(today_tasks)}")

# Mostrar TODAS las etiquetas únicas
print("\n2️⃣ Todas las etiquetas únicas encontradas:")
all_labels = set()
for task in today_tasks:
    labels = task.get('labels', [])
    all_labels.update(labels)

for label in sorted(all_labels):
    print(f"   - '{label}' (type: {type(label).__name__})")

# Buscar tareas que contengan "check" en alguna etiqueta
print("\n3️⃣ Tareas con 'check' en alguna etiqueta:")
check_tasks = []
for task in today_tasks:
    labels = task.get('labels', [])
    for label in labels:
        if 'check' in str(label).lower():
            check_tasks.append(task)
            break

print(f"   Total: {len(check_tasks)}")
if check_tasks:
    for i, task in enumerate(check_tasks, 1):
        print(f"\n   {i}. {task['content']}")
        print(f"      Etiquetas: {task.get('labels', [])}")
        print(f"      Etiquetas (repr): {repr(task.get('labels', []))}")
        # Mostrar cada etiqueta individualmente
        for j, label in enumerate(task.get('labels', [])):
            print(f"         [{j}] '{label}' - lowercase: '{str(label).lower()}' - type: {type(label).__name__}")

# Probar la función has_checks_label
print("\n4️⃣ Probando función has_checks_label():")

def has_checks_label(task):
    """Check if task has any variant of the 'checks' label"""
    labels = task.get("labels", [])
    # Convert all labels to lowercase for case-insensitive comparison
    labels_lower = [l.lower() for l in labels]
    checks_variants = ["checks", "check", "cheks", "chek"]
    return any(variant in labels_lower for variant in checks_variants)

checks_detected = [t for t in today_tasks if has_checks_label(t)]
print(f"   Tareas detectadas con has_checks_label(): {len(checks_detected)}")

if checks_detected:
    for task in checks_detected:
        print(f"   - {task['content']}: {task.get('labels')}")
else:
    print("   ⚠️ NINGUNA tarea detectada con has_checks_label()")
    print("\n   Probando manualmente con las primeras 5 tareas:")
    for i, task in enumerate(today_tasks[:5], 1):
        labels = task.get('labels', [])
        labels_lower = [l.lower() for l in labels]
        print(f"\n   Tarea {i}: {task['content']}")
        print(f"      labels: {labels}")
        print(f"      labels_lower: {labels_lower}")
        print(f"      'checks' in labels_lower: {'checks' in labels_lower}")
        print(f"      'check' in labels_lower: {'check' in labels_lower}")

print("\n" + "="*80)
print("✅ Debug completado")
print("="*80)
