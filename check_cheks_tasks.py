from todoist_client import TodoistClient
from config import get_config
import json

config = get_config()
client = TodoistClient(config["TODOIST_API_TOKEN"])

all_tasks = client.get_all_active_tasks()
formatted_tasks = client.format_tasks_for_display(all_tasks)

print("\n=== TAREAS CON ETIQUETA 'Cheks' ===\n")
cheks_tasks = [t for t in formatted_tasks if "Cheks" in t.get("labels", [])]

if cheks_tasks:
    for task in cheks_tasks:
        print(f"ID: {task['id']}")
        print(f"Contenido: {task['content']}")
        print(f"Fecha: {task.get('due_date', 'SIN FECHA')}")
        print(f"Etiquetas: {task.get('labels', [])}")
        print(f"Prioridad: {task.get('priority', 'N/A')}")
        print("-" * 50)
else:
    print("❌ No hay tareas con la etiqueta 'Cheks'")

print(f"\nTotal de tareas activas: {len(formatted_tasks)}")
print(f"Tareas con etiqueta 'Cheks': {len(cheks_tasks)}")
