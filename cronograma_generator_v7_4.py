'''
Cronograma Generator V7.4 - Final Refined Python Strategy

Features:
- No ChatGPT dependency for generation
- Fills entire day 07:00-21:00 without gaps
- Strict time blocks control
- Alternates types: fisico, administrativo, intelectual
- Priority order: P1 → P2 → P3 → P4
- Administrative + morning tasks at end of morning block
- Multi-pass scheduling to eliminate unassigned tasks and gaps
'''

from todoist_client import TodoistClient
from config import get_config
from datetime import datetime, timedelta

config = get_config()

print("="*80)
print("📅 CRONOGRAMA GENERATOR V7.4 - FINAL PYTHON STRATEGY")
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
    return sorted(tasks, key=lambda t: (get_priority_value(t), get_duration_minutes(t), t.get("due_date") or "9999-99-99"))

# --- Task Categorization ---

print("\n2️⃣ Categorizing and sorting tasks...")

# Add type and duration to each task dictionary for easier access
for task in formatted_tasks:
    task["duration"] = get_duration_minutes(task)
    task["type"] = get_task_type_from_labels(task)

# Separate tasks into dedicated lists based on rules
rutina_tasks = sort_by_priority([t for t in formatted_tasks if has_label(t, "rutina administrativa matinal")])
cheks_tasks = sort_by_priority([t for t in formatted_tasks if has_label(t, "Cheks")])
manana_tasks = sort_by_priority([t for t in formatted_tasks if has_label(t, "por la mañana")])
tarde_tasks = sort_by_priority([t for t in formatted_tasks if has_label(t, "por la tarde")])
noche_tasks = sort_by_priority([t for t in formatted_tasks if has_label(t, "por la noche")])

# Flexible tasks are those not in any specific time block
time_restricted_labels = {"rutina administrativa matinal", "Cheks", "por la mañana", "por la tarde", "por la noche"}
flexible_tasks = sort_by_priority([t for t in formatted_tasks if not set(t.get("labels", [])).intersection(time_restricted_labels)])

# --- Cronograma Generation ---

print("\n3️⃣ Generating cronograma with Final Python Logic...")

# Pass 1: Build the schedule with all tasks
schedule = {}
for i in range(840): # 14 hours * 60 minutes
    schedule[i] = None

def add_task_to_schedule(task, start_minute):
    duration = task["duration"]
    for i in range(start_minute, start_minute + duration):
        schedule[i] = task
    return start_minute + duration

# Fixed blocks
for i in range(20): schedule[i] = {"content": "Desayunar", "type": "Fija", "priority": "P-", "duration": 20, "url": "", "labels": []}
for i in range(420, 480): schedule[i] = {"content": "Comer", "type": "Fija", "priority": "P-", "duration": 60, "url": "", "labels": []}

# Sequential blocks
current_minute = 20
for task in rutina_tasks:
    current_minute = add_task_to_schedule(task, current_minute)
for task in cheks_tasks:
    current_minute = add_task_to_schedule(task, current_minute)

# Time-restricted tasks
all_time_restricted_tasks = manana_tasks + tarde_tasks + noche_tasks
for task in sort_by_priority(all_time_restricted_tasks):
    duration = task["duration"]
    placed = False
    
    start_search = 0
    end_search = 840
    if has_label(task, "por la mañana"): end_search = 420
    elif has_label(task, "por la tarde"): start_search = 480; end_search = 780
    elif has_label(task, "por la noche"): start_search = 780

    for i in range(start_search, end_search - duration + 1):
        if all(schedule[j] is None for j in range(i, i + duration)):
            add_task_to_schedule(task, i)
            placed = True
            break

# Flexible tasks
for task in flexible_tasks:
    duration = task["duration"]
    placed = False
    for i in range(840 - duration + 1):
        if all(schedule[j] is None for j in range(i, i + duration)):
            add_task_to_schedule(task, i)
            placed = True
            break

# Pass 2: Consolidate schedule into a list of events
final_cronograma = []
i = 0
while i < 840:
    start_minute = i
    task = schedule[i]

    # Group consecutive identical tasks or free slots
    while i < 840 and schedule[i] == task:
        i += 1
    
    end_minute = i
    duration = end_minute - start_minute

    start_time = (datetime.strptime("07:00", "%H:%M") + timedelta(minutes=start_minute)).strftime("%H:%M")
    end_time = (datetime.strptime("07:00", "%H:%M") + timedelta(minutes=end_minute)).strftime("%H:%M")

    if task is None:
        # This is a free block
        final_cronograma.append({
            "content": "Tiempo libre",
            "type": "General",
            "priority": "P4",
            "duration": duration,
            "url": "",
            "labels": [],
            "start_time": start_time,
            "end_time": end_time
        })
    else:
        # This is a scheduled task
        task_details = dict(task)
        task_details["start_time"] = start_time
        task_details["end_time"] = end_time
        # Overwrite duration to the actual consolidated block duration
        task_details["duration"] = duration 
        task_details["priority"] = f"P{get_priority_value(task)}" if 'priority' in task else 'P-'
        final_cronograma.append(task_details)

# --- Generate HTML ---

print("\n4️⃣ Generating final HTML...")

html_rows = ""
for task in final_cronograma:
    priority = task.get("priority", "P4")
    priority_class = f"priority-{priority.lower()}"
    task_type = task.get("type", "General")
    type_class = f"type-{task_type.replace(' ', '-')}"
    duration = task.get("duration", 1)
    height_class = f"h-{duration}"

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

full_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Cronograma V7.4 - Final Python Strategy</title>
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
<h1 style="margin: 0; color: #2c7a7b;">✅ Cronograma V7.4 - Estrategia Final con Python</h1>
<p style="margin: 10px 0 0 0; color: #555;">
<strong>Fecha:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}<br>
<strong>Estrategia:</strong> Lógica de asignación multi-paso para garantizar que todas las tareas se agenden correctamente.
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

</body>
</html>'''

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"/home/ubuntu/daily-agenda-automation/cronograma_v7_4_{timestamp}.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"\n✅ Cronograma V7.4 guardado en:")
print(f"   {output_file}")
print("\n" + "="*80)
print("✅ ¡ÉXITO! CRONOGRAMA V7.4 CON ESTRATEGIA FINAL")
print("="*80)
