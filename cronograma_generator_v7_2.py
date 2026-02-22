"""
Cronograma Generator V7.2 - Refined Pure Python Strategy

Features:
- No ChatGPT dependency for generation
- Fills entire day 07:00-21:00 without gaps
- Strict time blocks control
- Alternates types: fisico, administrativo, intelectual
- Priority order: P1 → P2 → P3 → P4
- Administrative + morning tasks at end of morning block
- Improved task placement logic to minimize unassigned tasks
"""

from todoist_client import TodoistClient
from config import get_config
from datetime import datetime, timedelta

config = get_config()

print("="*80)
print("📅 CRONOGRAMA GENERATOR V7.2 - REFINED PURE PYTHON STRATEGY")
print("="*80)

# Get ALL active tasks
print("\n1️⃣ Fetching ALL active tasks from Todoist...")
todoist_client = TodoistClient(config["TODOIST_API_TOKEN"])
all_tasks = todoist_client.get_all_active_tasks()
formatted_tasks = todoist_client.format_tasks_for_display(all_tasks)
print(f"✅ Found {len(formatted_tasks)} active tasks")

# --- Helper Functions ---
time_labels = ["5min", "5 minutos", "10min", "10 minutos", "15min", "15 minutos",
               "20min", "20 minutos", "30min", "30 minutos", "1h", "1 hora", "2h", "2 horas"]

def has_label(task, label):
    return label in task.get("labels", [])

def get_duration_minutes(task):
    labels = task.get("labels", [])
    for label in labels:
        if label in ["5min", "5 minutos"]: return 5
        if label in ["10min", "10 minutos"]: return 10
        if label in ["15min", "15 minutos"]: return 15
        if label in ["20min", "20 minutos"]: return 20
        if label in ["30min", "30 minutos"]: return 30
        if label in ["1h", "1 hora"]: return 60
        if label in ["2h", "2 horas"]: return 120
    return 20 # Default duration

def get_task_type_from_labels(task):
    labels = task.get("labels", [])
    if "fisico" in labels: return "Física"
    if "administrativo" in labels: return "Administrativa"
    if "intelectual" in labels: return "Intelectual"
    return "General" # Default type

def get_priority_value(task):
    priority = task.get("priority", 4)
    if isinstance(priority, str):
        return {"P1": 1, "P2": 2, "P3": 3, "P4": 4}.get(priority, 4)
    return priority

def sort_by_priority(tasks):
    return sorted(tasks, key=lambda t: (get_priority_value(t), t.get("due_date") or "9999-99-99"))

# --- Task Categorization ---

print("\n2️⃣ Categorizing and sorting tasks...")

# Add type and duration to each task dictionary for easier access
for task in formatted_tasks:
    task["duration"] = get_duration_minutes(task)
    task["type"] = get_task_type_from_labels(task)

# Separate tasks into dedicated lists based on rules
rutina_tasks = sort_by_priority([t for t in formatted_tasks if has_label(t, "rutina administrativa matinal")])
cheks_tasks = sort_by_priority([t for t in formatted_tasks if has_label(t, "Cheks")])
manana_tasks = sort_by_priority([t for t in formatted_tasks if has_label(t, "por la mañana") and t["type"] != "Administrativa"])
admin_morning_tasks = sort_by_priority([t for t in formatted_tasks if has_label(t, "por la mañana") and t["type"] == "Administrativa"])
tarde_tasks = sort_by_priority([t for t in formatted_tasks if has_label(t, "por la tarde")])
noche_tasks = sort_by_priority([t for t in formatted_tasks if has_label(t, "por la noche")])

# Flexible tasks are those not in any specific time block
time_restricted_labels = {"rutina administrativa matinal", "Cheks", "por la mañana", "por la tarde", "por la noche"}
flexible_tasks = sort_by_priority([t for t in formatted_tasks if not set(t.get("labels", [])).intersection(time_restricted_labels)])

# --- Cronograma Generation ---

print("\n3️⃣ Generating cronograma with Refined Pure Python Logic...")

cronograma = []
current_time = datetime.strptime("07:00", "%H:%M")
end_of_day = datetime.strptime("21:00", "%H:%M")
last_task_type = None

def add_task_to_schedule(task, start_time):
    duration = task["duration"]
    end_time = start_time + timedelta(minutes=duration)
    cronograma.append({
        "start_time": start_time.strftime("%H:%M"),
        "end_time": end_time.strftime("%H:%M"),
        "content": task.get("content"),
        "type": task["type"],
        "priority": f"P{get_priority_value(task)}",
        "labels": [l for l in task.get("labels", []) if l not in time_labels],
        "duration": duration,
        "url": task.get("url")
    })
    return end_time

# Fixed block: Desayunar
cronograma.append({"start_time": "07:00", "end_time": "07:20", "content": "Desayunar", "type": "Fija", "priority": "P-", "labels": [], "duration": 20, "url": ""})
current_time = datetime.strptime("07:20", "%H:%M")

# Sequential blocks: Rutina & Cheks
for task in rutina_tasks:
    current_time = add_task_to_schedule(task, current_time)
for task in cheks_tasks:
    current_time = add_task_to_schedule(task, current_time)

# --- Main Scheduling Loop ---

all_remaining_tasks = manana_tasks + admin_morning_tasks + tarde_tasks + noche_tasks + flexible_tasks
all_remaining_tasks = sort_by_priority(all_remaining_tasks)

last_type_count = 0

while current_time < end_of_day and all_remaining_tasks:
    # Skip lunch break
    if datetime.strptime("14:00", "%H:%M") <= current_time < datetime.strptime("15:00", "%H:%M"):
        cronograma.append({"start_time": "14:00", "end_time": "15:00", "content": "Comer", "type": "Fija", "priority": "P-", "labels": [], "duration": 60, "url": ""})
        current_time = datetime.strptime("15:00", "%H:%M")
        last_task_type = None # Reset type tracking after break
        last_type_count = 0
        continue

    # Determine valid task types for the current time slot
    if current_time < datetime.strptime("12:00", "%H:%M"): # Morning
        valid_tasks = [t for t in all_remaining_tasks if has_label(t, "por la mañana") or t in flexible_tasks]
    elif current_time < datetime.strptime("14:00", "%H:%M"): # Admin Morning
        valid_tasks = [t for t in all_remaining_tasks if (has_label(t, "por la mañana") and t["type"] == "Administrativa") or t in flexible_tasks]
    elif current_time < datetime.strptime("20:00", "%H:%M"): # Afternoon
        valid_tasks = [t for t in all_remaining_tasks if has_label(t, "por la tarde") or t in flexible_tasks]
    else: # Night
        valid_tasks = [t for t in all_remaining_tasks if has_label(t, "por la noche") or t in flexible_tasks]

    best_task = None
    # Try to find a task of a different type
    for task in valid_tasks:
        if task["type"] != last_task_type:
            best_task = task
            break
    
    # If not found, or if we can place another of the same type
    if not best_task and last_type_count < 2 and valid_tasks:
        best_task = valid_tasks[0]

    # If still no task, maybe we can only place a different type
    if not best_task and valid_tasks:
        for task in valid_tasks:
            if task["type"] != last_task_type:
                best_task = task
                break
        if not best_task: # If all valid tasks are the same type we can't place, take a flexible one
            for task in flexible_tasks:
                if task in all_remaining_tasks:
                    best_task = task
                    break

    if best_task and (current_time + timedelta(minutes=best_task["duration"])) <= end_of_day:
        current_time = add_task_to_schedule(best_task, current_time)
        all_remaining_tasks.remove(best_task)
        if best_task in flexible_tasks: flexible_tasks.remove(best_task)

        if best_task["type"] == last_task_type:
            last_type_count += 1
        else:
            last_type_count = 1
        last_task_type = best_task["type"]
    else:
        # If no task fits, create a buffer slot to prevent infinite loops
        cronograma.append({"start_time": current_time.strftime("%H:%M"), "end_time": (current_time + timedelta(minutes=15)).strftime("%H:%M"), "content": "Tiempo libre / Preparación", "type": "General", "priority": "P4", "labels": [], "duration": 15, "url": ""})
        current_time += timedelta(minutes=15)
        last_task_type = None # Reset type tracking
        last_type_count = 0

# --- Generate HTML ---

print("\n4️⃣ Generating final HTML...")

# Sort cronograma by start time before rendering
cronograma.sort(key=lambda x: datetime.strptime(x["start_time"], "%H:%M"))

html_rows = ""
for task in cronograma:
    priority = task.get("priority", "P4")
    priority_class = f"priority-{priority.lower()}"
    task_type = task.get("type", "General")
    type_class = f"type-{task_type.replace(' ', '-')}"
    duration = task.get("duration", 20)
    height_class = f"h-{duration}" # Simplified height class

    labels_html = "".join(f'<span class="label">{l}</span>' for l in task.get("labels", []))

    html_rows += f'''        <tr class="{priority_class}">
          <td class="{height_class}">{task["start_time"]}-{task["end_time"]}</td>
          <td><a href="{task["url"]}" target="_blank">{task["content"]}</a></td>
          <td class="{type_class}">{task_type}</td>
          <td class="priority-cell {priority_class}">{priority}</td>
          <td>{labels_html}</td>
          <td>{duration} min</td>
        </tr>
'''

# Unassigned tasks
unassigned_tasks_html = ""
if all_remaining_tasks:
    unassigned_tasks_html = "<h2>📋 Tareas Pendientes no Asignadas</h2><table><thead><tr><th>Actividad</th><th>Prioridad</th><th>Etiquetas</th></tr></thead><tbody>"
    for task in all_remaining_tasks:
        priority = f"P{get_priority_value(task)}"
        labels = ", ".join([l for l in task.get("labels", []) if l not in time_labels])
        unassigned_tasks_html += f"<tr><td><a href=\"{task['url']}\" target=\"_blank\">{task['content']}</a></td><td>{priority}</td><td>{labels}</td></tr>"
    unassigned_tasks_html += "</tbody></table>"


full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Cronograma V7.2 - Refined Python</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; background: #f0f2f5; color: #333; }}
  table {{ border-collapse: collapse; width: 100%; max-width: 1000px; margin: 20px auto; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  thead {{ background: #4a5568; color: white; }}
  th, td {{ border: 1px solid #e2e8f0; padding: 10px 14px; vertical-align: middle; text-align: left; }}
  tr:nth-child(even) {{ background: #f7fafc; }}
  a {{ color: #2b6cb0; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .label {{ background: #edf2f7; color: #4a5568; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-right: 5px; }}
  
  /* --- Type Colors (Background) --- */
  .type-Física {{ background-color: #d1e7dd; }} .type-Intelectual {{ background-color: #cff4fc; }} .type-Administrativa {{ background-color: #fff3cd; }} .type-Fija {{ background-color: #d9ead3; }} .type-General {{ background-color: #e2e8f0; }}

  /* --- Priority Colors (Border) --- */
  .priority-p1 {{ border-left: 5px solid #e53e3e; }} .priority-p2 {{ border-left: 5px solid #dd6b20; }} .priority-p3 {{ border-left: 5px solid #3182ce; }} .priority-p4 {{ border-left: 2px solid #a0aec0; }} .priority-p- {{ border-left: 2px solid #a0aec0; }}

  /* --- Priority Cell (Background) --- */
  .priority-cell {{ text-align: center; font-weight: bold; color: white; }}
  .priority-cell.priority-p1 {{ background-color: #e53e3e; }} .priority-cell.priority-p2 {{ background-color: #dd6b20; }} .priority-cell.priority-p3 {{ background-color: #3182ce; }} .priority-cell.priority-p4 {{ background-color: #a0aec0; }}

</style>
</head>
<body>
<div style="background-color: #e6fffa; padding: 15px; margin-bottom: 20px; border-left: 5px solid #38b2ac;">
<h1 style="margin: 0; color: #2c7a7b;">✅ Cronograma V7.2 - Estrategia Python Refinada</h1>
<p style="margin: 10px 0 0 0; color: #555;">
<strong>Fecha:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}<br>
<strong>Estrategia:</strong> Lógica de asignación mejorada para minimizar tareas no asignadas y asegurar el llenado del día.
</p>
</div>

<table>
  <thead>
    <tr><th>Hora</th><th>Actividad</th><th>Tipo</th><th>Prioridad</th><th>Etiquetas</th><th>Duración</th></tr>
  </thead>
  <tbody>
    {html_rows}
  </tbody>
</table>

{unassigned_tasks_html}

</body>
</html>"""

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"/home/ubuntu/daily-agenda-automation/cronograma_v7_2_{timestamp}.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"\n✅ Cronograma V7.2 guardado en:")
print(f"   {output_file}")
print("\n" + "="*80)
print("✅ ¡ÉXITO! CRONOGRAMA V7.2 CON LÓGICA REFINADA")
print("="*80)
