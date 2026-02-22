"""
Cronograma Generator V7.1 - Pure Python Strategy
Features:
- No ChatGPT dependency for generation
- Fills entire day 07:00-21:00 without gaps
- Strict time blocks control
- Alternates types: fisico, administrativo, intelectual
- Priority order: P1 → P2 → P3 → P4
- Administrative + morning tasks at end of morning block
"""

from todoist_client import TodoistClient
from config import get_config
from datetime import datetime, timedelta

config = get_config()

print("="*80)
print("📅 CRONOGRAMA GENERATOR V7.1 - PURE PYTHON STRATEGY")
print("="*80)

# Get ALL active tasks
print("\n1️⃣ Fetching ALL active tasks from Todoist...")
todoist_client = TodoistClient(config["TODOIST_API_TOKEN"])
all_tasks = todoist_client.get_all_active_tasks()
formatted_tasks = todoist_client.format_tasks_for_display(all_tasks)
print(f"✅ Found {len(formatted_tasks)} active tasks")

# Helper functions
time_labels = ["5min", "5 minutos", "10min", "10 minutos", "15min", "15 minutos",
               "20min", "20 minutos", "30min", "30 minutos", "1h", "1 hora", "2h", "2 horas"]
type_labels = ["fisico", "administrativo", "intelectual"]

def has_non_time_labels(task):
    labels = task.get("labels", [])
    non_time_labels = [l for l in labels if l not in time_labels]
    return len(non_time_labels) > 0

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
    return 20

def get_task_type_from_labels(task):
    labels = task.get("labels", [])
    if "fisico" in labels: return "Física"
    if "administrativo" in labels: return "Administrativa"
    if "intelectual" in labels: return "Intelectual"
    return "Sin tipo"

def get_priority_value(task):
    priority = task.get("priority", 4)
    if isinstance(priority, str):
        priority_map = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
        priority = priority_map.get(priority, 4)
    return priority

def sort_by_priority(tasks):
    return sorted(tasks, key=lambda t: (get_priority_value(t), t.get("due_date") or "9999-99-99"))

# Filter tasks with labels
filtered_tasks = [t for t in formatted_tasks if has_non_time_labels(t)]

# Separate tasks by time blocks
rutina_tasks = [t for t in filtered_tasks if has_label(t, "rutina administrativa matinal")]
cheks_tasks = [t for t in filtered_tasks if has_label(t, "Cheks")]
manana_tasks = [t for t in filtered_tasks if has_label(t, "por la mañana")]
tarde_tasks = [t for t in filtered_tasks if has_label(t, "por la tarde")]
noche_tasks = [t for t in filtered_tasks if has_label(t, "por la noche")]

# Separate administrative tasks for end of morning
admin_morning_tasks = [t for t in manana_tasks if get_task_type_from_labels(t) == "Administrativa"]
manana_tasks = [t for t in manana_tasks if get_task_type_from_labels(t) != "Administrativa"]

# Flexible tasks
time_restricted_labels = {"rutina administrativa matinal", "Cheks", "por la mañana", "por la tarde", "por la noche"}
flexible_tasks = [t for t in filtered_tasks if not set(t.get("labels", [])).intersection(time_restricted_labels)]

# Sort all blocks by priority
rutina_tasks = sort_by_priority(rutina_tasks)
cheks_tasks = sort_by_priority(cheks_tasks)
manana_tasks = sort_by_priority(manana_tasks)
admin_morning_tasks = sort_by_priority(admin_morning_tasks)
tarde_tasks = sort_by_priority(tarde_tasks)
noche_tasks = sort_by_priority(noche_tasks)
flexible_tasks = sort_by_priority(flexible_tasks)

# --- PURE PYTHON CRONOGRAMA GENERATION ---

print("\n2️⃣ Generating cronograma with Pure Python...")

cronograma = []
current_time = datetime.strptime("07:00", "%H:%M")
end_of_day = datetime.strptime("21:00", "%H:%M")

# Add Desayunar
cronograma.append({
    "start_time": "07:00",
    "end_time": "07:20",
    "content": "Desayunar",
    "type": "Fija",
    "priority": "P-",
    "labels": [],
    "duration": 20,
    "url": ""
})
current_time += timedelta(minutes=20)

# Alternating task placement algorithm
def place_tasks_alternating(tasks, start_time, end_time):
    schedule = []
    current_t = start_time
    last_type = None
    last_type_count = 0
    
    tasks_to_process = list(tasks)

    while tasks_to_process and current_t < end_time:
        best_task = None
        best_task_index = -1

        # Find best task to alternate
        for i, task in enumerate(tasks_to_process):
            task_type = get_task_type_from_labels(task)
            if task_type != last_type:
                best_task = task
                best_task_index = i
                break
        
        # If no alternating task, take the first one (max 2 of same type)
        if not best_task and last_type_count < 2:
            best_task = tasks_to_process[0]
            best_task_index = 0
        elif not best_task:
            # Find a different type if possible
            for i, task in enumerate(tasks_to_process):
                if get_task_type_from_labels(task) != last_type:
                    best_task = task
                    best_task_index = i
                    break
            if not best_task: # Still no different type, take first one
                best_task = tasks_to_process[0]
                best_task_index = 0

        duration = get_duration_minutes(best_task)
        if current_t + timedelta(minutes=duration) <= end_time:
            task_type = get_task_type_from_labels(best_task)
            schedule.append({
                "start_time": current_t.strftime("%H:%M"),
                "end_time": (current_t + timedelta(minutes=duration)).strftime("%H:%M"),
                "content": best_task.get("content"),
                "type": task_type,
                "priority": f"P{get_priority_value(best_task)}",
                "labels": [l for l in best_task.get("labels", []) if l not in time_labels],
                "duration": duration,
                "url": best_task.get("url")
            })
            current_t += timedelta(minutes=duration)
            tasks_to_process.pop(best_task_index)
            
            if task_type == last_type:
                last_type_count += 1
            else:
                last_type_count = 1
            last_type = task_type
        else:
            tasks_to_process.pop(best_task_index) # Remove task that doesn't fit
            
    return schedule, tasks_to_process, current_t

# --- Build cronograma block by block ---

# Rutina
schedule, rutina_tasks, current_time = place_tasks_alternating(rutina_tasks, current_time, end_of_day)
cronograma.extend(schedule)

# Cheks
schedule, cheks_tasks, current_time = place_tasks_alternating(cheks_tasks, current_time, end_of_day)
cronograma.extend(schedule)

# Mañana (until 12:00)
end_morning = datetime.strptime("12:00", "%H:%M")
schedule, manana_tasks, current_time = place_tasks_alternating(manana_tasks, current_time, end_morning)
cronograma.extend(schedule)

# Admin Mañana (12:00-14:00)
end_admin_morning = datetime.strptime("14:00", "%H:%M")
current_time = max(current_time, end_morning) # Start at 12:00
schedule, admin_morning_tasks, current_time = place_tasks_alternating(admin_morning_tasks, current_time, end_admin_morning)
cronograma.extend(schedule)

# Comer
current_time = max(current_time, end_admin_morning)
cronograma.append({
    "start_time": "14:00",
    "end_time": "15:00",
    "content": "Comer",
    "type": "Fija",
    "priority": "P-",
    "labels": [],
    "duration": 60,
    "url": ""
})
current_time = datetime.strptime("15:00", "%H:%M")

# Tarde (15:00-20:00)
end_tarde = datetime.strptime("20:00", "%H:%M")
schedule, tarde_tasks, current_time = place_tasks_alternating(tarde_tasks, current_time, end_tarde)
cronograma.extend(schedule)

# Noche (20:00-21:00)
end_noche = datetime.strptime("21:00", "%H:%M")
current_time = max(current_time, end_tarde)
schedule, noche_tasks, current_time = place_tasks_alternating(noche_tasks, current_time, end_noche)
cronograma.extend(schedule)

# Fill remaining time with flexible tasks
remaining_tasks = rutina_tasks + cheks_tasks + manana_tasks + admin_morning_tasks + tarde_tasks + noche_tasks + flexible_tasks
remaining_tasks = sort_by_priority(remaining_tasks)

schedule, remaining_tasks, current_time = place_tasks_alternating(remaining_tasks, current_time, end_of_day)
cronograma.extend(schedule)

# --- Generate HTML ---

print("\n3️⃣ Generating final HTML...")

html_rows = ""
for task in cronograma:
    priority = task.get("priority", "P4")
    priority_class = f"priority-{priority.lower()}"
    
    task_type = task.get("type", "Sin tipo")
    type_class = f"type-{task_type.replace(' ', '-')}"

    duration = task.get("duration", 20)
    height_class = ""
    if duration <= 10: height_class = "h-10"
    elif duration <= 15: height_class = "h-15"
    elif duration <= 20: height_class = "h-20"
    elif duration <= 30: height_class = "h-30"
    elif duration <= 60: height_class = "h-60"
    else: height_class = "h-120"

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
if remaining_tasks:
    unassigned_tasks_html = "<h2>📋 Tareas Pendientes no Asignadas</h2><table><thead><tr><th>Actividad</th><th>Prioridad</th><th>Etiquetas</th></tr></thead><tbody>"
    for task in remaining_tasks:
        priority = f"P{get_priority_value(task)}"
        labels = ", ".join([l for l in task.get("labels", []) if l not in time_labels])
        unassigned_tasks_html += f"<tr><td><a href=\"{task['url']}\" target=\"_blank\">{task['content']}</a></td><td>{priority}</td><td>{labels}</td></tr>"
    unassigned_tasks_html += "</tbody></table>"


full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Cronograma V7.1 - Pure Python</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; background: #f0f2f5; color: #333; }}
  table {{ border-collapse: collapse; width: 100%; max-width: 1000px; margin: 20px auto; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
  thead {{ background: #4a5568; color: white; }}
  th, td {{ border: 1px solid #e2e8f0; padding: 10px 14px; vertical-align: middle; text-align: left; }}
  tr:nth-child(even) {{ background: #f7fafc; }}
  a {{ color: #2b6cb0; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .label {{ background: #edf2f7; color: #4a5568; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-right: 5px; }}
  
  /* --- Heights -- */
  .h-10 {{ height: 30px; }} .h-15 {{ height: 35px; }} .h-20 {{ height: 45px; }} .h-30 {{ height: 60px; }} .h-60 {{ height: 90px; }} .h-120 {{ height: 150px; }}

  /* --- Type Colors (Background) --- */
  .type-Física {{ background-color: #d1e7dd; }} .type-Intelectual {{ background-color: #cff4fc; }} .type-Administrativa {{ background-color: #fff3cd; }} .type-Fija {{ background-color: #d9ead3; }}

  /* --- Priority Colors (Border) --- */
  .priority-p1 {{ border-left: 5px solid #e53e3e; }} /* Red */
  .priority-p2 {{ border-left: 5px solid #dd6b20; }} /* Orange */
  .priority-p3 {{ border-left: 5px solid #3182ce; }} /* Blue */
  .priority-p4 {{ border-left: 2px solid #a0aec0; }} /* Gray */

  /* --- Priority Cell (Background) --- */
  .priority-cell {{ text-align: center; font-weight: bold; color: white; }}
  .priority-cell.priority-p1 {{ background-color: #e53e3e; }}
  .priority-cell.priority-p2 {{ background-color: #dd6b20; }}
  .priority-cell.priority-p3 {{ background-color: #3182ce; }}
  .priority-cell.priority-p4 {{ background-color: #a0aec0; }}

</style>
</head>
<body>
<div style="background-color: #e6fffa; padding: 15px; margin-bottom: 20px; border-left: 5px solid #38b2ac;">
<h1 style="margin: 0; color: #2c7a7b;">✅ Cronograma V7.1 - Estrategia 100% Python</h1>
<p style="margin: 10px 0 0 0; color: #555;">
<strong>Fecha:</strong> {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}<br>
<strong>Estrategia:</strong> Generación 100% Python para control total. Sin dependencia de ChatGPT para la estructura.
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
output_file = f"/home/ubuntu/daily-agenda-automation/cronograma_v7_1_{timestamp}.html"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"\n✅ Cronograma V7.1 guardado en:")
print(f"   {output_file}")
print("\n" + "="*80)
print("✅ ¡ÉXITO! CRONOGRAMA V7.1 CON ESTRATEGIA 100% PYTHON")
print("="*80)
