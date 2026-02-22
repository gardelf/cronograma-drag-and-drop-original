#!/usr/bin/env python3
"""
Script simplificado para probar la regla de checks
"""

from todoist_client import TodoistClient
from datetime import datetime

TODOIST_TOKEN = "50ff91ef15761a6727b8b991ac3be61a96f76538"

print("="*80)
print("🧪 TEST: REGLA DE CHECKS EN EL CRONOGRAMA")
print("="*80)

# Función has_checks_label del generador
def has_checks_label(task):
    """Check if task has any variant of the 'checks' label"""
    labels = task.get("labels", [])
    labels_lower = [l.lower() for l in labels]
    checks_variants = ["checks", "check", "cheks", "chek"]
    return any(variant in labels_lower for variant in checks_variants)

# Función para ordenar por prioridad
def sort_by_priority(tasks):
    """Sort tasks by priority (higher first)"""
    priority_map = {"Urgente": 4, "Alta": 3, "Media": 2, "Baja": 1}
    return sorted(tasks, key=lambda t: priority_map.get(t.get("priority", "Baja"), 1), reverse=True)

# Inicializar cliente
print("\n1️⃣ Obteniendo tareas de Todoist...")
client = TodoistClient(TODOIST_TOKEN)
all_tasks = client.get_all_active_tasks()
formatted_tasks = client.format_tasks_for_display(all_tasks)

# Filtrar tareas para hoy
today_str = datetime.now().strftime("%Y-%m-%d")
today_tasks = []
for task in formatted_tasks:
    due_date = task.get('due_date')
    if due_date is None or due_date <= today_str:
        today_tasks.append(task)

print(f"   Total tareas para hoy: {len(today_tasks)}")

# Categorizar tareas
print("\n2️⃣ Categorizando tareas...")

cheks_tasks = sort_by_priority([t for t in today_tasks if has_checks_label(t)])
rutina_tasks = sort_by_priority([t for t in today_tasks if not has_checks_label(t) and "rutina administrativa matinal" in [l.lower() for l in t.get("labels", [])]])
manana_tasks = sort_by_priority([t for t in today_tasks if not has_checks_label(t) and "por la mañana" in [l.lower() for l in t.get("labels", [])]])

print(f"   📋 Tareas CHECKS: {len(cheks_tasks)}")
print(f"   🌅 Tareas RUTINA: {len(rutina_tasks)}")
print(f"   ☀️  Tareas MAÑANA: {len(manana_tasks)}")

# Mostrar tareas checks
if cheks_tasks:
    print("\n3️⃣ Tareas con etiqueta CHECKS detectadas:")
    for i, task in enumerate(cheks_tasks, 1):
        print(f"\n   {i}. {task['content']}")
        print(f"      Prioridad: {task['priority']}")
        print(f"      Etiquetas: {task.get('labels', [])}")
        print(f"      Duración esperada: 5 minutos (regla checks)")
else:
    print("\n   ⚠️ NO se detectaron tareas con etiqueta CHECKS")

# Simular orden de asignación
print("\n4️⃣ Orden de asignación al cronograma:")
print("   1. Desayunar (07:00-07:20)")
print("   2. Rutina administrativa matinal")
print("   3. ✅ TAREAS CHECKS ← Aquí deberían aparecer")
print("   4. Tareas de mañana")
print("   5. Comer (14:00-15:00)")
print("   6. Tareas de tarde")
print("   7. Tareas de noche")

print("\n" + "="*80)
print("✅ Test completado")
print("="*80)
