'''
Cronograma Generator V7.5 - Morning Alternation Rule (Fixed)

Features:
- No ChatGPT dependency for generation
- Fills entire day 07:00-21:00 without gaps
- Strict time blocks control
- Morning rule: NO two physical tasks in a row. Must be 1 intellectual + 1 physical, or 2 intellectual + 1 physical
- Priority order: P1 → P2 → P3 → P4
- Administrative + morning tasks at end of morning block
- Multi-pass scheduling to eliminate unassigned tasks and gaps
'''

from todoist_client import TodoistClient
from calendar_client import iCloudCalendarClient
from config import get_config
from ics_exporter import ICSExporter
from event_detector import detect_new_events_in_shared_calendar
from events_db import get_new_events
from datetime import datetime, timedelta
import json
import os
import sys

config = get_config()

# Check if --tomorrow flag is passed
generate_for_tomorrow = '--tomorrow' in sys.argv
target_date = datetime.now() + timedelta(days=1) if generate_for_tomorrow else datetime.now()

print("="*80)
print("📅 CRONOGRAMA GENERATOR V7.5 - MORNING ALTERNATION RULE (FIXED)")
if generate_for_tomorrow:
    print(f"🕒 Generando cronograma para MAÑANA: {target_date.strftime('%d/%m/%Y')}")
else:
    print(f"🕒 Generando cronograma para HOY: {target_date.strftime('%d/%m/%Y')}")
print("="*80)

# Detect new events in shared calendar
print("\n1️⃣ Detecting new events in shared calendar...")
new_events_detected = detect_new_events_in_shared_calendar("Casa Juana Doña", days_ahead=30)
print(f"✅ Detected {len(new_events_detected)} new events")

# Get pending new events from database
new_events_pending = get_new_events()
print(f"📋 Pending new events for review: {len(new_events_pending)}")

# Get calendar events from PERSONAL calendar (highest priority)
print("\n2️⃣ Fetching events from YOUR personal calendar...")
# Load .env explicitly to ensure iCloud credentials are available
from config import load_env_file
load_env_file()
calendar_client = iCloudCalendarClient()
calendar_events = calendar_client.get_today_events(target_date=target_date)
print(f"✅ Found {len(calendar_events)} calendar events in your personal calendar")

# Get ALL active tasks from Todoist and filter by target date
print("\n3️⃣ Fetching active tasks from Todoist...")
todoist_client = TodoistClient(config["TODOIST_API_TOKEN"])
all_tasks = todoist_client.get_all_active_tasks()
formatted_tasks = todoist_client.format_tasks_for_display(all_tasks)

# Filter tasks to only include those due on target_date or without due date
target_date_str = target_date.strftime("%Y-%m-%d")
filtered_tasks = []
for task in formatted_tasks:
    due_date = task.get('due_date')
    # Include tasks that:
    # 1. Have no due date (can be scheduled anytime)
    # 2. Have due date matching target_date
    # 3. Have due date in the past (overdue tasks)
    if due_date is None:
        filtered_tasks.append(task)
    elif due_date <= target_date_str:
        filtered_tasks.append(task)

formatted_tasks = filtered_tasks
print(f"✅ Found {len(formatted_tasks)} tasks for {target_date_str} (filtered from {len(all_tasks)} total)")

# Load completed tasks from local database
print("\n   📋 Loading completed tasks from local database...")
from completed_tasks_db import get_completed_tasks_for_date, cleanup_old_tasks

# Clean up old completed tasks (older than 7 days)
cleanup_old_tasks(days_to_keep=7)

# Get completed tasks for today
completed_tasks = get_completed_tasks_for_date(target_date_str)
print(f"   ✅ Found {len(completed_tasks)} completed tasks for {target_date_str}")

if completed_tasks:
    for task in completed_tasks:
        print(f"      ✅ {task['start_time']}-{task['end_time']}: {task['content']} (completada)")

# Note: completed_tasks will be used later when generating the HTML schedule

# --- Helper Functions ---
time_labels = ["5min", "5 minutos", "10min", "10 minutos", "15min", "15 minutos",
               "20min", "20 minutos", "30min", "30 minutos", "1h", "1 hora", "2h", "2 horas"]

def has_label(task, label):
    return label in task.get("labels", [])

def has_checks_label(task):
    """Check if task has any variant of the 'checks' label"""
    labels = task.get("labels", [])
    # Convert all labels to lowercase for case-insensitive comparison
    labels_lower = [l.lower() for l in labels]
    checks_variants = ["checks", "check", "cheks", "chek"]
    return any(variant in labels_lower for variant in checks_variants)

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
    
    # Default duration: 5 min for checks tasks, 20 min for others
    if has_checks_label(task):
        return 5
    return 20

def get_task_type_from_labels(task):
    labels = task.get("labels", [])
    if "fisico" in labels: return "Física"
    if "administrativo" in labels: return "Administrativa"
    if "intelectual" in labels: return "Intelectual"
    return "General" # Default type

def get_priority_value(task):
    """Get numeric priority value for sorting (lower is higher priority)"""
    priority = task.get("priority_value", 1)  # Use priority_value from formatted tasks
    if isinstance(priority, str):
        return {"P1": 1, "P2": 2, "P3": 3, "P4": 4}.get(priority, 4)
    # Todoist uses 4=urgent, 3=high, 2=medium, 1=low
    # We need to sort by this value (higher number = higher priority)
    # So we return negative to sort correctly
    return 5 - priority  # Convert: 4→1, 3→2, 2→3, 1→4

def sort_by_priority(tasks):
    return sorted(tasks, key=lambda t: (get_priority_value(t), get_duration_minutes(t), t.get("due_date") or "9999-99-99"))

# --- Task Categorization ---

print("\n4️⃣ Categorizing and sorting tasks...")

# Add type and duration to each task dictionary for easier access
for task in formatted_tasks:
    task["duration"] = get_duration_minutes(task)
    task["type"] = get_task_type_from_labels(task)

# Separate tasks into dedicated lists based on rules
# PRIORITY 1: Checks tasks - these ALWAYS go to rutina administrativa, regardless of other labels
cheks_tasks = sort_by_priority([t for t in formatted_tasks if has_checks_label(t)])
print(f"   🔍 Found {len(cheks_tasks)} tasks with checks labels")
if cheks_tasks:
    for task in cheks_tasks:
        print(f"      - {task['content']} (labels: {task.get('labels', [])})")

# PRIORITY 2: Other time-specific tasks (excluding those already in checks)
rutina_tasks = sort_by_priority([t for t in formatted_tasks 
                                 if has_label(t, "rutina administrativa matinal") 
                                 and not has_checks_label(t)])
manana_tasks = sort_by_priority([t for t in formatted_tasks 
                                 if has_label(t, "por la mañana") 
                                 and not has_checks_label(t)])
tarde_tasks = sort_by_priority([t for t in formatted_tasks 
                               if has_label(t, "por la tarde") 
                               and not has_checks_label(t)])
noche_tasks = sort_by_priority([t for t in formatted_tasks 
                               if has_label(t, "por la noche") 
                               and not has_checks_label(t)])

# Flexible tasks are those not in any specific time block and not checks
time_restricted_base = {"rutina administrativa matinal", "por la mañana", "por la tarde", "por la noche"}
flexible_tasks = sort_by_priority([t for t in formatted_tasks 
                                   if not set(t.get("labels", [])).intersection(time_restricted_base) 
                                   and not has_checks_label(t)])

# --- Cronograma Generation ---

print("\n5️⃣ Generating cronograma with Morning Alternation Rule...")

# Pass 1: Build the schedule with all tasks
schedule = {}
for i in range(840): # 14 hours * 60 minutes
    schedule[i] = None

def add_task_to_schedule_at(task, start_minute):
    """Add a task at a specific minute, skipping calendar events"""
    duration = task["duration"]
    for i in range(start_minute, start_minute + duration):
        # Don't overwrite calendar events (they have 'content' starting with emoji)
        if schedule[i] is None or (isinstance(schedule[i], dict) and not schedule[i].get('content', '').startswith('📅')):
            schedule[i] = task
    return start_minute + duration

# Fixed blocks - Calendar events have HIGHEST priority
print("   Adding calendar events as fixed blocks...")
for event in calendar_events:
    # Convert time to minutes from 07:00
    start_hour, start_min = map(int, event['start_time'].split(':'))
    start_minute = (start_hour - 7) * 60 + start_min
    
    # Only add if within our schedule range (07:00-21:00)
    if 0 <= start_minute < 840:
        duration = event['duration']
        for i in range(start_minute, min(start_minute + duration, 840)):
            schedule[i] = event
        print(f"      ✅ {event['start_time']}-{event['end_time']}: {event['content']}")

# Fixed blocks - Desayunar and Comer
for i in range(20): schedule[i] = {"content": "Desayunar", "type": "Fija", "priority": "P-", "duration": 20, "url": "", "labels": []}
for i in range(420, 480): schedule[i] = {"content": "Comer", "type": "Fija", "priority": "P-", "duration": 60, "url": "", "labels": []}

# NEW: Schedule tasks with specific due_time first (like calendar events)
print("\n   Scheduling tasks with specific due_time...")
tasks_with_time = [t for t in formatted_tasks if t.get('due_time')]
tasks_without_time = [t for t in formatted_tasks if not t.get('due_time')]

for task in tasks_with_time:
    due_time = task['due_time']
    try:
        # Convert due_time to minutes from 07:00
        hour, minute = map(int, due_time.split(':'))
        start_minute = (hour - 7) * 60 + minute
        
        # Only schedule if within range (07:00-21:00)
        if 0 <= start_minute < 840:
            duration = task['duration']
            
            # Check if the time slot is available
            slot_available = all(schedule[i] is None for i in range(start_minute, min(start_minute + duration, 840)))
            
            if slot_available:
                # Schedule at the specific time
                for i in range(start_minute, min(start_minute + duration, 840)):
                    schedule[i] = task
                print(f"      ✅ {due_time}: {task['content']} (horario fijo)")
            else:
                # Conflict detected, will be scheduled sequentially later
                print(f"      ⚠️ {due_time}: {task['content']} (conflicto, se programará secuencialmente)")
                # Add back to the list for sequential scheduling
                tasks_without_time.append(task)
        else:
            print(f"      ⚠️ {due_time}: {task['content']} (fuera de rango 07:00-21:00)")
            tasks_without_time.append(task)
    except Exception as e:
        print(f"      ❌ Error procesando {task['content']}: {e}")
        tasks_without_time.append(task)

# Update task lists to only include tasks without time (or those that couldn't be scheduled)
rutina_tasks = [t for t in rutina_tasks if t in tasks_without_time]
cheks_tasks = [t for t in cheks_tasks if t in tasks_without_time]
manana_tasks = [t for t in manana_tasks if t in tasks_without_time]
tarde_tasks = [t for t in tarde_tasks if t in tasks_without_time]
noche_tasks = [t for t in noche_tasks if t in tasks_without_time]

# Sequential blocks
current_minute = 20
for task in rutina_tasks:
    current_minute = add_task_to_schedule_at(task, current_minute)
for task in cheks_tasks:
    current_minute = add_task_to_schedule_at(task, current_minute)

# Morning tasks with special alternation rule
# Rule: NO two physical tasks in a row. Must be 1 intellectual + 1 physical, or 2 intellectual + 1 physical
print("\n   Applying morning alternation rule...")

# Separate morning tasks by type
morning_fisica = [t for t in manana_tasks if t["type"] == "Física"]
morning_intelectual = [t for t in manana_tasks if t["type"] == "Intelectual"]
morning_other = [t for t in manana_tasks if t["type"] not in ["Física", "Intelectual"]]

# Build morning schedule with strict alternation
# Strategy: Distribute physical tasks evenly, always separated by 1-2 intellectual tasks
morning_schedule = []
fisica_idx = 0
intelectual_idx = 0

num_fisica = len(morning_fisica)
num_intelectual = len(morning_intelectual)

# Calculate how many intellectual tasks should go between each physical task
if num_fisica > 0:
    intelectual_per_fisica = num_intelectual // num_fisica
    extra_intelectual = num_intelectual % num_fisica
else:
    intelectual_per_fisica = 0
    extra_intelectual = num_intelectual

print(f"   Distribution: {num_intelectual} intelectual / {num_fisica} física = {intelectual_per_fisica} per física + {extra_intelectual} extra")

# Interleave tasks
while fisica_idx < num_fisica:
    # Add 1 or 2 intellectual tasks before each physical
    tasks_to_add = max(1, min(2, intelectual_per_fisica))
    
    for _ in range(tasks_to_add):
        if intelectual_idx < num_intelectual:
            morning_schedule.append(morning_intelectual[intelectual_idx])
            intelectual_idx += 1
    
    # Add one physical task
    morning_schedule.append(morning_fisica[fisica_idx])
    fisica_idx += 1

# Add any remaining intellectual tasks at the end
while intelectual_idx < num_intelectual:
    morning_schedule.append(morning_intelectual[intelectual_idx])
    intelectual_idx += 1

print(f"   Morning schedule: {len(morning_schedule)} tasks")
print(f"   Sequence: {' → '.join([t['type'] for t in morning_schedule])}")

# Place morning tasks sequentially in the morning block
morning_start = current_minute
for task in morning_schedule:
    duration = task["duration"]
    if current_minute + duration <= 420: # Ensure it fits before lunch
        current_minute = add_task_to_schedule_at(task, current_minute)
    else:
        print(f"   ⚠️ Task '{task['content']}' doesn't fit in morning block")

# Place other morning tasks (General, Administrativa) in remaining morning slots
for task in morning_other:
    duration = task["duration"]
    placed = False
    for i in range(morning_start, 420 - duration + 1):
        if all(schedule[j] is None for j in range(i, i + duration)):
            add_task_to_schedule_at(task, i)
            placed = True
            break
    if not placed:
        print(f"   ⚠️ Could not place morning task: {task['content']}")

# Afternoon tasks
for task in tarde_tasks:
    duration = task["duration"]
    placed = False
    for i in range(480, 780 - duration + 1):
        if all(schedule[j] is None for j in range(i, i + duration)):
            add_task_to_schedule_at(task, i)
            placed = True
            break

# Night tasks
for task in noche_tasks:
    duration = task["duration"]
    placed = False
    for i in range(780, 840 - duration + 1):
        if all(schedule[j] is None for j in range(i, i + duration)):
            add_task_to_schedule_at(task, i)
            placed = True
            break

# Flexible tasks
for task in flexible_tasks:
    duration = task["duration"]
    placed = False
    for i in range(840 - duration + 1):
        if all(schedule[j] is None for j in range(i, i + duration)):
            add_task_to_schedule_at(task, i)
            placed = True
            break

# Insert completed tasks into schedule
print("\n   📋 Inserting completed tasks into schedule...")
for completed_task in completed_tasks:
    try:
        # Parse start and end times
        start_hour, start_min = map(int, completed_task['start_time'].split(':'))
        end_hour, end_min = map(int, completed_task['end_time'].split(':'))
        
        # Convert to minutes from 07:00
        start_minute = (start_hour - 7) * 60 + start_min
        end_minute = (end_hour - 7) * 60 + end_min
        
        # Only insert if within schedule range
        if 0 <= start_minute < 840 and 0 <= end_minute <= 840:
            # Insert completed task into schedule
            for i in range(start_minute, end_minute):
                schedule[i] = {
                    'id': completed_task['id'],
                    'content': completed_task['content'],
                    'priority_value': 1,  # Default
                    'labels': completed_task['labels'],
                    'url': '',
                    'completed': True,  # Mark as completed
                    'duration': end_minute - start_minute
                }
            print(f"      ✅ Inserted: {completed_task['start_time']}-{completed_task['end_time']}: {completed_task['content']}")
    except Exception as e:
        print(f"      ❌ Error inserting completed task: {e}")

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
        # Convert Todoist priority to P1-P4 display format
        # Todoist: 4=urgent, 3=high, 2=medium, 1=low
        # Display: P1=urgent, P2=high, P3=medium, P4=low
        todoist_priority = task.get("priority_value", 1)
        display_priority = 5 - todoist_priority  # Convert: 4→P1, 3→P2, 2→P3, 1→P4
        task_details["priority"] = f"P{display_priority}"
        final_cronograma.append(task_details)

# --- Identify Unassigned Tasks ---

print("\n5️⃣ Identifying unassigned tasks...")

# Collect all tasks that were scheduled
scheduled_task_ids = set()
for minute, task in schedule.items():
    if task and isinstance(task, dict) and task.get("content") not in ["Desayunar", "Comer", "Tiempo libre"]:
        task_id = task.get("id") or task.get("content")
        if task_id:
            scheduled_task_ids.add(task_id)

# Find unassigned tasks
unassigned_tasks = []
for task in formatted_tasks:
    task_id = task.get("id") or task.get("content")
    if task_id not in scheduled_task_ids:
        unassigned_tasks.append(task)

print(f"   Total tasks: {len(formatted_tasks)}")
print(f"   Scheduled tasks: {len(scheduled_task_ids)}")
print(f"   Unassigned tasks: {len(unassigned_tasks)}")

# Find tasks with FUTURE date that are not in the schedule and not recurring
# Tasks with today's date or past dates are already included in filtered_tasks above
tasks_with_date = []
for task in all_tasks:  # Use all_tasks from Todoist API (before filtering)
    task_id = task.get("id") or task.get("content")
    due = task.get("due")
    
    # Check if task has a date, is not recurring, and is not in schedule
    if (due and 
        due.get("date") and 
        not due.get("is_recurring", False) and 
        task_id not in scheduled_task_ids):
        
        # Only include tasks with FUTURE dates (after target_date)
        task_due_date = due.get("date")
        if task_due_date > target_date_str:
            # Format the task for display
            formatted_task = {
                "id": task.get("id"),
                "content": task.get("content", "Sin título"),
                "due_date": task_due_date,
                "priority": todoist_client._get_priority_label(task.get("priority", 1)),
                "priority_value": task.get("priority", 1),
                "labels": task.get("labels", [])
            }
            tasks_with_date.append(formatted_task)

# Sort by date
tasks_with_date.sort(key=lambda t: t["due_date"])
print(f"   Tasks with FUTURE date (not recurring, not scheduled): {len(tasks_with_date)}")

# --- Generate HTML ---

print("\n6️⃣ Generating final HTML...")

def get_time_block_color(start_time):
    """Determine time block and return background color based on start time"""
    hour = int(start_time.split(':')[0])
    minute = int(start_time.split(':')[1])
    time_minutes = hour * 60 + minute
    
    # Define time blocks (in minutes from midnight)
    desayuno_start = 7 * 60  # 07:00
    desayuno_end = 7 * 60 + 20  # 07:20
    
    rutina_admin_start = 7 * 60 + 20  # 07:20
    rutina_admin_end = 9 * 60 + 40  # 09:40
    
    manana_start = 9 * 60 + 40  # 09:40
    manana_end = 14 * 60  # 14:00
    
    comida_start = 14 * 60  # 14:00
    comida_end = 15 * 60  # 15:00
    
    tarde_start = 15 * 60  # 15:00
    tarde_end = 20 * 60  # 20:00
    
    noche_start = 20 * 60  # 20:00
    noche_end = 21 * 60  # 21:00
    
    # Assign colors based on time block
    if desayuno_start <= time_minutes < desayuno_end:
        return '#fffaf5', 'Desayuno'  # Very light peach
    elif rutina_admin_start <= time_minutes < rutina_admin_end:
        return '#f0f7ff', 'Rutina administrativa matinal'  # Very light blue
    elif manana_start <= time_minutes < manana_end:
        return '#f8fcf5', 'Por la mañana'  # Very light green
    elif comida_start <= time_minutes < comida_end:
        return '#fffef0', 'Comida'  # Very light yellow
    elif tarde_start <= time_minutes < tarde_end:
        return '#fef8fa', 'Por la tarde'  # Very light pink
    elif noche_start <= time_minutes < noche_end:
        return '#f8f7fc', 'Noche'  # Very light purple
    else:
        return '#ffffff', 'Otro'  # White for any other time

def get_emoji_for_task(content, task_type):
    """Select appropriate emoji based on task content and type"""
    content_lower = content.lower()
    
    # Check content keywords first
    if any(word in content_lower for word in ['desayun', 'comer', 'cenar', 'comida']):
        return '🍽️'
    if any(word in content_lower for word in ['agua', 'beber', 'hidrat']):
        return '💧'
    if any(word in content_lower for word in ['email', 'correo', 'gmail']):
        return '📧'
    if any(word in content_lower for word in ['leer', 'lectura', 'libro', 'padre rico']):
        return '📚'
    if any(word in content_lower for word in ['tradear', 'trading', 'replay', 'tesla', 'nvidia', 'analisis']):
        return '📈'
    if any(word in content_lower for word in ['fondos', 'fondear', 'dinero', 'pago', 'interbroker']):
        return '💰'
    if any(word in content_lower for word in ['espalda', 'hombro', 'pecho', 'ejercicio', 'físico']):
        return '💪'
    if any(word in content_lower for word in ['bateria', 'música', 'instrumento']):
        return '🥁'
    if any(word in content_lower for word in ['gracias', 'dios', 'mantra', 'recordatorio']):
        return '🙏'
    if any(word in content_lower for word in ['control', 'gastos', 'presupuesto']):
        return '💳'
    if any(word in content_lower for word in ['visita', 'idealista', 'garage', 'plaza']):
        return '🏠'
    if any(word in content_lower for word in ['checks', 'check', 'revisar']):
        return '✅'
    if any(word in content_lower for word in ['constructor', 'contacto', 'llamar']):
        return '📞'
    if any(word in content_lower for word in ['libre', 'descanso']):
        return '⏸️'
    
    # Fallback to task type
    if task_type == 'Física':
        return '💪'
    elif task_type == 'Intelectual':
        return '🧠'
    elif task_type == 'Administrativa':
        return '📋'
    elif task_type == 'Fija':
        return '📌'
    else:
        return '📝'

# Load Idealista data
idealista_section = ''
firefly_section = ''

try:
    from idealista_postgres import get_idealista_comparison
    
    print("🔍 Cargando datos de Idealista con comparación")
    current_data, previous_data = get_idealista_comparison()
    
    if current_data and current_data.get('properties'):
        properties_html = ''
        current_props = {p.get('propertyId'): p for p in current_data.get('properties', [])}
        previous_props = {p.get('propertyId'): p for p in previous_data.get('properties', [])} if previous_data else {}
        
        for prop_id, current_prop in current_props.items():
            prop_name = current_prop.get('propertyName', f'Propiedad {prop_id}')
            
            # Current values
            current_visitas = current_prop.get('visitas', 0)
            current_favoritos = current_prop.get('favoritos', 0)
            current_mensajes = current_prop.get('mensajes', 0)
            current_date = current_data.get('timestamp', 'Hoy')
            
            # Previous values and comparison
            if prop_id in previous_props:
                prev_prop = previous_props[prop_id]
                prev_visitas = prev_prop.get('visitas', 0)
                prev_favoritos = prev_prop.get('favoritos', 0)
                prev_mensajes = prev_prop.get('mensajes', 0)
                prev_date = previous_data.get('timestamp', 'Anterior')
                
                # Calculate differences
                diff_visitas = current_visitas - prev_visitas
                diff_favoritos = current_favoritos - prev_favoritos
                diff_mensajes = current_mensajes - prev_mensajes
                
                # Calculate percentages
                pct_visitas = (diff_visitas / prev_visitas * 100) if prev_visitas > 0 else 0
                pct_favoritos = (diff_favoritos / prev_favoritos * 100) if prev_favoritos > 0 else 0
                pct_mensajes = (diff_mensajes / prev_mensajes * 100) if prev_mensajes > 0 else 0
                
                def format_comparison(current, previous, diff, pct):
                    color = '#38a169' if diff > 0 else ('#e53e3e' if diff < 0 else '#718096')
                    arrow = '↑' if diff > 0 else ('↓' if diff < 0 else '→')
                    sign = '+' if diff > 0 else ''
                    return f'''
                    <div style="text-align: center; padding: 10px; background: #f7fafc; border-radius: 6px;">
                        <div style="font-size: 28px; font-weight: bold; color: {color}; margin-bottom: 5px;">{current}</div>
                        <div style="font-size: 11px; color: #a0aec0; margin-bottom: 8px;">Anterior: {previous}</div>
                        <div style="font-size: 14px; font-weight: 600; color: {color};">{sign}{diff} ({sign}{pct:.1f}%) {arrow}</div>
                    </div>
                    '''
                
                visitas_html = format_comparison(current_visitas, prev_visitas, diff_visitas, pct_visitas)
                favoritos_html = format_comparison(current_favoritos, prev_favoritos, diff_favoritos, pct_favoritos)
                mensajes_html = format_comparison(current_mensajes, prev_mensajes, diff_mensajes, pct_mensajes)
                
                comparison_info = f'''
                <div style="background: #edf2f7; padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 12px;">
                    <strong>📅 Hoy:</strong> {current_date} | <strong>📆 Anterior:</strong> {prev_date}
                </div>
                '''
            else:
                # No previous data for this property
                visitas_html = f'<div style="text-align: center; padding: 10px;"><div style="font-size: 28px; font-weight: bold; color: #3182ce;">{current_visitas}</div><div style="font-size: 11px; color: #a0aec0;">Sin datos anteriores</div></div>'
                favoritos_html = f'<div style="text-align: center; padding: 10px;"><div style="font-size: 28px; font-weight: bold; color: #e53e3e;">{current_favoritos}</div><div style="font-size: 11px; color: #a0aec0;">Sin datos anteriores</div></div>'
                mensajes_html = f'<div style="text-align: center; padding: 10px;"><div style="font-size: 28px; font-weight: bold; color: #38a169;">{current_mensajes}</div><div style="font-size: 11px; color: #a0aec0;">Sin datos anteriores</div></div>'
                comparison_info = f'<div style="background: #edf2f7; padding: 8px 12px; border-radius: 6px; margin-bottom: 12px; font-size: 12px;"><strong>📅 Hoy:</strong> {current_date}</div>'
            
            properties_html += f'''
            <div style="background: white; padding: 18px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.12);">
                <h3 style="margin: 0 0 12px 0; color: #2d3748; font-size: 18px; font-weight: 700;">🏠 {prop_name}</h3>
                <p style="margin: 0 0 10px 0; color: #718096; font-size: 11px;">Código: {prop_id}</p>
                {comparison_info}
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
                    <div>
                        <div style="font-size: 11px; color: #718096; margin-bottom: 6px; text-align: center; font-weight: 600;">👁️ VISITAS</div>
                        {visitas_html}
                    </div>
                    <div>
                        <div style="font-size: 11px; color: #718096; margin-bottom: 6px; text-align: center; font-weight: 600;">❤️ FAVORITOS</div>
                        {favoritos_html}
                    </div>
                    <div>
                        <div style="font-size: 11px; color: #718096; margin-bottom: 6px; text-align: center; font-weight: 600;">💬 MENSAJES</div>
                        {mensajes_html}
                    </div>
                </div>
            </div>
            '''
        
        idealista_section = f'''
<div class="card" id="idealista-stats-section">
    <div class="section-title">🏠 Estadísticas de Idealista</div>
    <p class="subtext" style="margin-bottom: 16px;">Última actualización: {current_data.get('last_updated', 'Hoy')}</p>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 18px;">
        {properties_html}
    </div>
</div>
'''
        print(f"✅ Sección de Idealista con comparación generada correctamente")
except Exception as e:
    print(f"⚠️ Error loading Idealista data: {e}")
    idealista_section = f'''
<div class="card" style="background: #fff3cd; border-left: 5px solid #ffc107;">
    <div class="section-title">⚠️ DEBUG: Error cargando Idealista</div>
    <p>Error: {e}</p>
    <p>Archivo buscado: {idealista_file if 'idealista_file' in locals() else 'No definido'}</p>
    <p>¿Existe? {os.path.exists(idealista_file) if 'idealista_file' in locals() else 'No se pudo verificar'}</p>
</div>
'''

# Load Firefly III data
try:
    from firefly_client import FireflyClient
    from datetime import datetime
    import calendar
    from config import load_env_file
    
    # Ensure .env is loaded
    load_env_file()
    
    firefly_client = FireflyClient()
    firefly_data = firefly_client.get_summary()
    
    if firefly_data:
        current_month = firefly_data.get('current_month', {})
        previous_month = firefly_data.get('previous_month', {})
        weekly = firefly_data.get('weekly', {})
        weekly_detail = firefly_data.get('weekly_detail', [])
        last_updated = firefly_data.get('last_updated', 'Nunca')
        
        # Current month data
        current_expenses = current_month.get('expenses', 0)
        current_currency = current_month.get('currency', 'EUR')
        now = datetime.now()
        current_month_name = calendar.month_name[now.month]
        
        # Previous month data
        previous_expenses = previous_month.get('expenses', 0)
        previous_currency = previous_month.get('currency', 'EUR')
        prev_month_num = now.month - 1 if now.month > 1 else 12
        previous_month_name = calendar.month_name[prev_month_num]
        
        # Weekly data
        weekly_expenses = weekly.get('expenses', 0)
        weekly_currency = weekly.get('currency', 'EUR')
        
        # Next month extraordinary expenses
        next_month_extraordinary = firefly_data.get('next_month_extraordinary', [])
        next_month_num = now.month + 1 if now.month < 12 else 1
        next_month_name = calendar.month_name[next_month_num]
        
        # Calculate total extraordinary expenses
        total_extraordinary = sum(expense.get('amount', 0) for expense in next_month_extraordinary)
        extraordinary_currency = next_month_extraordinary[0].get('currency', 'EUR') if next_month_extraordinary else 'EUR'
        
        # Generate transactions detail HTML
        transactions_html = ''
        if weekly_detail:
            for trans in weekly_detail:
                date = trans.get('date', '')
                description = trans.get('description', '')
                amount = trans.get('amount', 0)
                category = trans.get('category', 'Sin categoría')
                currency = trans.get('currency', 'EUR')
                
                transactions_html += f'''
                <div style="padding: 10px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-weight: bold; color: #1f2937;">{description}</div>
                        <div style="font-size: 12px; color: #6b7280;">{date} • {category}</div>
                    </div>
                    <div style="font-size: 18px; font-weight: bold; color: #e53e3e;">{amount:,.2f} {currency}</div>
                </div>
                '''
        else:
            transactions_html = '<div style="padding: 20px; text-align: center; color: #6b7280;">No hay gastos en los últimos 7 días</div>'
        
        # Generate extraordinary expenses detail HTML
        extraordinary_html = ''
        if next_month_extraordinary:
            for expense in next_month_extraordinary:
                description = expense.get('description', '')
                date = expense.get('date', '')
                amount = expense.get('amount', 0)
                currency = expense.get('currency', 'EUR')
                
                extraordinary_html += f'''
                <div style="padding: 10px; border-bottom: 1px solid #e5e7eb; display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-weight: bold; color: #1f2937;">{description}</div>
                        <div style="font-size: 12px; color: #6b7280;">{date}</div>
                    </div>
                    <div style="font-size: 18px; font-weight: bold; color: #f59e0b;">{amount:,.2f} {currency}</div>
                </div>
                '''
        else:
            extraordinary_html = '<div style="padding: 20px; text-align: center; color: #6b7280;">No hay gastos extraordinarios registrados para el próximo mes</div>'
        
        firefly_section = f'''
<div class="card" id="firefly-stats-section">
    <div class="section-title" style="cursor: pointer;" onclick="toggleFireflySection()">
        💰 Firefly III - Finanzas <span id="firefly-toggle-icon">▼</span>
    </div>
    <p class="subtext" style="margin-bottom: 16px;">Última actualización: {last_updated}</p>
    
    <div id="firefly-content" style="display: block;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin-bottom: 20px;">
            <!-- Mes Actual -->
            <div style="background: #f9fafb; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb;">
                <div class="subtext" style="margin-bottom: 8px;">📅 {current_month_name} {now.year}</div>
                <div style="text-align: center;">
                    <div class="metric" style="color: #ef4444;">{current_expenses:,.2f}</div>
                    <div class="subtext" style="margin-top: 4px;">📉 Total Gastos</div>
                    <div class="subtext" style="font-size: 12px; margin-top: 4px;">{current_currency}</div>
                </div>
            </div>
            
            <!-- Mes Anterior -->
            <div style="background: #f9fafb; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb;">
                <div class="subtext" style="margin-bottom: 8px;">📅 {previous_month_name}</div>
                <div style="text-align: center;">
                    <div class="metric" style="color: #ef4444;">{previous_expenses:,.2f}</div>
                    <div class="subtext" style="margin-top: 4px;">📉 Total Gastos</div>
                    <div class="subtext" style="font-size: 12px; margin-top: 4px;">{previous_currency}</div>
                </div>
            </div>
            
            <!-- Últimos 7 Días -->
            <div style="background: #f9fafb; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb;">
                <div class="subtext" style="margin-bottom: 8px; cursor: pointer;" onclick="toggleWeeklyDetail()">
                    📅 Últimos 7 Días <span id="weekly-toggle-icon">▼</span>
                </div>
                <div style="text-align: center;">
                    <div class="metric" style="color: #ef4444;">{weekly_expenses:,.2f}</div>
                    <div class="subtext" style="margin-top: 4px;">📉 Gastos</div>
                    <div class="subtext" style="font-size: 12px; margin-top: 4px;">{weekly_currency}</div>
                </div>
            </div>
            
            <!-- Gastos Extraordinarios Mes Siguiente -->
            <div style="background: #f9fafb; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb;">
                <div class="subtext" style="margin-bottom: 8px; cursor: pointer;" onclick="toggleExtraordinaryDetail()">
                    💎 Extraordinarios {next_month_name} <span id="extraordinary-toggle-icon">▼</span>
                </div>
                <div style="text-align: center;">
                    <div class="metric" style="color: #f59e0b;">{total_extraordinary:,.2f}</div>
                    <div class="subtext" style="margin-top: 4px;">💰 Total Extraordinario</div>
                    <div class="subtext" style="font-size: 12px; margin-top: 4px;">{extraordinary_currency}</div>
                </div>
            </div>
        </div>
        
        <!-- Detalle de Gastos Semanales (Desplegable) -->
        <div id="weekly-detail" style="display: none; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 15px;">
            <h3 style="margin: 0 0 15px 0; color: #065f46; font-size: 18px;">📋 Detalle de Gastos (Últimos 7 Días)</h3>
            <div style="max-height: 400px; overflow-y: auto;">
                {transactions_html}
            </div>
        </div>
        
        <!-- Detalle de Gastos Extraordinarios (Desplegable) -->
        <div id="extraordinary-detail" style="display: none; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-top: 15px;">
            <h3 style="margin: 0 0 15px 0; color: #f59e0b; font-size: 18px;">💎 Gastos Extraordinarios para {next_month_name}</h3>
            <div style="max-height: 400px; overflow-y: auto;">
                {extraordinary_html}
            </div>
        </div>
    </div>
</div>

<script>
function toggleFireflySection() {{
    var content = document.getElementById('firefly-content');
    var icon = document.getElementById('firefly-toggle-icon');
    if (content.style.display === 'none') {{
        content.style.display = 'block';
        icon.textContent = '▼';
    }} else {{
        content.style.display = 'none';
        icon.textContent = '▶';
    }}
}}

function toggleWeeklyDetail() {{
    var detail = document.getElementById('weekly-detail');
    var icon = document.getElementById('weekly-toggle-icon');
    if (detail.style.display === 'none') {{
        detail.style.display = 'block';
        icon.textContent = '▲';
    }} else {{
        detail.style.display = 'none';
        icon.textContent = '▼';
    }}
}}

function toggleExtraordinaryDetail() {{
    var detail = document.getElementById('extraordinary-detail');
    var icon = document.getElementById('extraordinary-toggle-icon');
    if (detail.style.display === 'none') {{
        detail.style.display = 'block';
        icon.textContent = '▲';
    }} else {{
        detail.style.display = 'none';
        icon.textContent = '▼';
    }}
}}
</script>
'''
except Exception as e:
    print(f"⚠️ Error loading Firefly data: {e}")
    import traceback
    traceback.print_exc()
    import os
    print(f"DEBUG: FIREFLY_URL = {os.getenv('FIREFLY_URL')}")
    print(f"DEBUG: FIREFLY_TOKEN exists = {bool(os.getenv('FIREFLY_TOKEN'))}")
    print(f"DEBUG: FIREFLY_TOKEN length = {len(os.getenv('FIREFLY_TOKEN', ''))}")
    firefly_section = ''

# Generate new events section HTML FIRST
if new_events_pending:
    new_events_html = '''
<div class="card" style="background: #f8fafc; border-left: 4px solid #94a3b8;">
  <div class="section-title" style="color: #475569;">
    🆕 Eventos Nuevos en Calendario Compartido
  </div>
  <p class="subtext" style="margin-bottom: 16px; color: #64748b;">
    ⚠️ Estos eventos están en <strong>"Casa Juana Doña"</strong> pero NO en tu calendario personal.<br>
    ⚠️ Decide si te afectan y cópialos si es necesario. El cronograma se regenerará automáticamente.
  </p>
  <div style="display: grid; gap: 15px;">
'''
    
    for event in new_events_pending:
        event_html = f'''
    <div style="background: white; border-radius: 8px; padding: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); border-left: 4px solid #94a3b8;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div style="flex: 1;">
          <h3 style="margin: 0 0 8px 0; color: #1f2937; font-size: 18px;">📅 {event['summary']}</h3>
          <p style="margin: 0; color: #6b7280; font-size: 15px;">
            🕐 <strong>{event['date']} {event['start_time']} - {event['end_time']}</strong>
          </p>
          <p style="margin: 5px 0 0 0; color: #9ca3af; font-size: 13px;">
            Detectado: {event['detected_at'][:10]}
          </p>
        </div>
        <div style="display: flex; gap: 10px;">
          <button onclick="copyAndRegenerate('{event['uid']}', '{event['summary']}')" 
                  style="background: #10b981; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: 600; transition: all 0.2s;" 
                  onmouseover="this.style.background='#059669'" 
                  onmouseout="this.style.background='#10b981'">
            📋 Copiar y regenerar cronograma
          </button>
          <button onclick="ignoreEvent('{event['uid']}')" 
                  style="background: #6b7280; color: white; border: none; padding: 12px 20px; border-radius: 6px; cursor: pointer; font-size: 15px; font-weight: 600; transition: all 0.2s;" 
                  onmouseover="this.style.background='#4b5563'" 
                  onmouseout="this.style.background='#6b7280'">
            ❌ Ignorar
          </button>
        </div>
      </div>
    </div>
'''
        new_events_html += event_html
    
    new_events_html += '''
  </div>
</div>

<script>
async function copyAndRegenerate(uid, summary) {
    const button = event.target;
    button.disabled = true;
    button.textContent = '⏳ Copiando...';
    
    showLoadingOverlay('Copiando evento a tu calendario personal...');
    
    try {
        const response = await fetch('/copy-and-regenerate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ uid: uid })
        });
        
        const result = await response.json();
        
        if (result.success && result.reload) {
            showSuccessMessage(`✅ Evento "${summary}" copiado correctamente`);
            setTimeout(() => { window.location.reload(); }, 2000);
        } else {
            throw new Error(result.error || 'Error desconocido');
        }
    } catch (error) {
        hideLoadingOverlay();
        button.disabled = false;
        button.textContent = '❌ Error - Reintentar';
        alert(`❌ Error: ${error.message}`);
    }
}

async function ignoreEvent(uid) {
    if (!confirm('¿Estás seguro de que quieres ignorar este evento?')) return;
    
    try {
        const response = await fetch('/ignore-event', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ uid: uid })
        });
        
        const result = await response.json();
        if (result.success) {
            showLoadingOverlay('Evento ignorado. Regenerando cronograma...');
            
            // Regenerate cronograma
            const regenResponse = await fetch('/generate-cronograma');
            const regenResult = await regenResponse.json();
            
            if (regenResult.success) {
                window.location.reload();
            } else {
                alert('⚠️ Evento ignorado pero no se pudo regenerar el cronograma');
                window.location.reload();
            }
        } else {
            throw new Error(result.error);
        }
    } catch (error) {
        alert(`❌ Error: ${error.message}`);
    }
}

function showLoadingOverlay(message) {
    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; justify-content: center; align-items: center; z-index: 9999;">
            <div style="background: white; padding: 40px; border-radius: 10px; text-align: center; max-width: 400px;">
                <div style="border: 4px solid #f3f4f6; border-top: 4px solid #3b82f6; border-radius: 50%; width: 50px; height: 50px; animation: spin 1s linear infinite; margin: 0 auto 20px;"></div>
                <h2 style="margin: 0 0 10px 0; color: #1f2937;">${message}</h2>
                <p style="margin: 0; color: #6b7280;">Regenerando cronograma...</p>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
    const style = document.createElement('style');
    style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
    document.head.appendChild(style);
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.remove();
}

function showSuccessMessage(message) {
    hideLoadingOverlay();
    const successDiv = document.createElement('div');
    successDiv.style.cssText = `position: fixed; top: 20px; right: 20px; background: #10b981; color: white; padding: 20px 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); z-index: 10000; font-size: 16px; font-weight: 600;`;
    successDiv.textContent = message;
    document.body.appendChild(successDiv);
}
</script>
'''
    new_events_section = new_events_html
else:
    new_events_section = ''

html_rows = ""
for task in final_cronograma:
    priority = task.get("priority", "P4")
    priority_class = f"priority-{priority.lower()}"
    task_type = task.get("type", "General")
    type_class = f"type-{task_type.replace(' ', '-')}"
    duration = task.get("duration", 1)
    
    # Map duration to height class
    if duration <= 5:
        height_class = "h-5"
    elif duration <= 10:
        height_class = "h-10"
    elif duration <= 15:
        height_class = "h-15"
    elif duration <= 20:
        height_class = "h-20"
    elif duration <= 30:
        height_class = "h-30"
    else:
        height_class = "h-60"
    
    # Get emoji for task
    content = task.get("content", "")
    emoji = get_emoji_for_task(content, task_type)
    
    # Truncate long titles and add tooltip
    if len(content) > 50:
        truncated_content = content[:47] + "..."
        content_escaped = content.replace('"', '&quot;').replace("'", '&#39;')
        content_html = f'{emoji} <span class="truncate" data-full-text="{content_escaped}">{truncated_content}</span>'
    else:
        content_html = f'{emoji} {content}'
    
    # Add link to Todoist if task has an ID (Todoist task)
    task_id = task.get("id")
    if task_id and task.get("source") != "calendar" and content not in ["Desayunar", "Comer", "Tiempo libre"]:
        todoist_url = f"https://todoist.com/app/task/{task_id}"
        content_html = f'<a href="{todoist_url}" target="_blank" style="color: #374151; text-decoration: none; font-weight: 500;">{content_html}</a>'
    # Add link if custom URL exists
    elif task.get("url"):
        url = task["url"]
        content_html = f'<a href="{url}" target="_blank">{content_html}</a>'
    
    # Generate labels HTML
    labels = task.get("labels", [])
    labels_html = ''.join(f'<span class="label">{l}</span>' for l in labels)
    labels_container = f'<div class="labels-container">{labels_html}</div>' if labels_html else ''
    
    # Get time block color
    time_color, time_block_name = get_time_block_color(task["start_time"])
    
    # Format time range with different sizes - wrapped in badge
    time_range_html = f'<span class="time-badge"><span class="time-start">{task["start_time"]}</span><span class="time-separator">-</span><span class="time-end">{task["end_time"]}</span></span>'
    
    # Create priority badge
    priority_num = priority.lower().replace('p', '')
    priority_badge_html = f'<span class="priority-badge {priority.lower()}">{priority}</span>'
    
    # Check if task is completed
    is_completed = task.get("completed", False)
    
    # Add checkbox only for Todoist tasks (not calendar events or fixed blocks)
    task_id = task.get("id")
    if task_id and task.get("source") != "calendar" and content not in ["Desayunar", "Comer", "Tiempo libre"]:
        if is_completed:
            # Completed task: checked and disabled checkbox
            checkbox_html = f'<input type="checkbox" class="task-checkbox" checked disabled title="Tarea completada">'
        else:
            # Active task: normal checkbox with data attributes
            # Escape content for HTML attribute
            content_escaped = content.replace('"', '&quot;').replace("'", '&#39;')
            labels_json = json.dumps(task.get("labels", [])).replace('"', '&quot;')
            checkbox_html = f'<input type="checkbox" class="task-checkbox" data-task-id="{task_id}" data-content="{content_escaped}" data-start-time="{task["start_time"]}" data-end-time="{task["end_time"]}" data-priority="{priority}" data-labels="{labels_json}" title="Marcar como completada">'
    else:
        checkbox_html = ''
    
    # Add completed-task class if task is completed
    completed_class = "completed-task" if is_completed else ""
    
    # Check if task has "check" or "checks" label
    has_check_label = any(label.lower() in ['check', 'checks'] for label in labels)
    check_class = "has-check-label" if has_check_label else ""
    
    html_rows += f'''        <tr class="{priority_class} {height_class} {completed_class} {check_class}">
          <td class="checkbox-col">{checkbox_html}</td>
          <td class="time-col" style="background-color: {time_color};">{time_range_html}</td>
          <td class="activity-col">{content_html}</td>
          <td class="priority-cell priority-col">{priority_badge_html}</td>
          <td class="duration-col" style="background-color: {time_color};"><span class="duration-badge">{duration} min</span></td>
          <td class="labels-col">{labels_container}</td>
        </tr>
'''

# Generate unassigned tasks HTML
if unassigned_tasks:
    # Custom sorting: Priority first, then for P4 tasks, those with ANY labels first
    def sort_unassigned_tasks(task):
        priority_value = task.get("priority_value", 1)
        display_priority = 5 - priority_value  # Convert to P1-P4
        
        # Check if task has ANY labels
        labels = task.get("labels", [])
        has_any_label = len(labels) > 0
        
        # For P4 tasks (priority_value=1), sort those with ANY labels first
        if priority_value == 1:  # P4 tasks
            # Return tuple: (priority, has_label inverted so True comes first)
            return (display_priority, not has_any_label)
        else:
            # For other priorities, just sort by priority
            return (display_priority, False)
    
    unassigned_html_rows = ""
    sorted_tasks = sorted(unassigned_tasks, key=sort_unassigned_tasks)
    
    # Debug: Print first 5 P4 tasks to verify sorting
    p4_count = 0
    for task in sorted_tasks:
        if task.get("priority_value") == 1 and p4_count < 5:
            labels = task.get("labels", [])
            print(f"   P4: {task.get('content', '')[:40]} → Labels: {len(labels)} → {labels[:2] if labels else 'NO LABELS'}")
            p4_count += 1
    
    # Track if we need to add separator line between P4 with labels and P4 without labels
    separator_added = False
    prev_task_priority = None
    prev_task_has_labels = None
    
    for task in sorted_tasks:
        priority_value = task.get("priority_value", 1)
        display_priority = 5 - priority_value
        priority = f"P{display_priority}"
        priority_class = f"priority-{priority.lower()}"
        
        content = task.get("content", "")
        task_type = task.get("type", "General")
        emoji = get_emoji_for_task(content, task_type)
        
        if task.get("url"):
            content_html = f'<a href="{task["url"]}" target="_blank">{emoji} {content}</a>'
        else:
            content_html = f'{emoji} {content}'
        
        labels = task.get("labels", [])
        has_labels = len(labels) > 0
        labels_html = ''.join(f'<span class="label">{l}</span>' for l in labels)
        labels_container = f'<div class="labels-container">{labels_html}</div>' if labels_html else ''
        
        # Add separator line when transitioning from P4 with labels to P4 without labels
        if (priority_value == 1 and  # Current task is P4
            prev_task_priority == 1 and  # Previous task was also P4
            prev_task_has_labels and  # Previous task had labels
            not has_labels and  # Current task has no labels
            not separator_added):  # Haven't added separator yet
            
            unassigned_html_rows += '''        <tr style="border-top: 3px solid #ffc107;">
          <td colspan="4" style="padding: 0; height: 3px; background: #ffc107;"></td>
        </tr>
'''
            separator_added = True
        
        # Update tracking variables
        prev_task_priority = priority_value
        prev_task_has_labels = has_labels
        
        duration = task.get("duration", 20)
        priority_badge_html = f'<span class="priority-badge {priority.lower()}">{priority}</span>'
        
        unassigned_html_rows += f'''        <tr class="{priority_class}">
          <td class="activity-col">{content_html}</td>
          <td class="priority-cell priority-col">{priority_badge_html}</td>
          <td class="duration-col">{duration} min</td>
          <td class="labels-col">{labels_container}</td>
        </tr>
'''
    
    unassigned_tasks_section = f'''
<div class="card" style="background: #fffbeb; border-left: 4px solid #f59e0b;">
  <div class="section-title" style="color: #92400e;">⚠️ Tareas Sin Asignar ({len(unassigned_tasks)})</div>
  <p class="subtext" style="margin-bottom: 16px; color: #78350f;">Estas tareas de Todoist no entraron en el cronograma de hoy:</p>
  <table>
    <thead>
      <tr><th>Actividad</th><th>P</th><th>Duración</th><th>Etiquetas</th></tr>
    </thead>
    <tbody>
{unassigned_html_rows}    </tbody>
  </table>
</div>
'''
else:
    unassigned_tasks_section = ''

# Generate tasks with date section
if tasks_with_date:
    tasks_with_date_html_rows = ""
    for task in tasks_with_date:
        content = task.get("content", "")
        task_id = task.get("id", "")
        due_date = task.get("due_date", "")
        priority = task.get("priority", "P4")
        priority_value = task.get("priority_value", 1)
        labels = task.get("labels", [])
        
        # Format date for display (YYYY-MM-DD -> DD/MM/YYYY)
        try:
            date_obj = datetime.strptime(due_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d/%m/%Y")
        except:
            formatted_date = due_date
        
        # Priority badge
        display_priority = 5 - priority_value
        priority_class = f"p{display_priority}"
        priority_badge_html = f'<span class="priority-badge {priority_class.lower()}">{priority}</span>'
        
        # Labels
        labels_html = ''.join(f'<span class="label">{l}</span>' for l in labels)
        labels_container = f'<div class="labels-container">{labels_html}</div>' if labels_html else ''
        
        # Create Todoist URL
        todoist_url = f"https://todoist.com/app/task/{task_id}" if task_id else "#"
        content_html = f'<a href="{todoist_url}" target="_blank" style="color: #64748b; text-decoration: none; font-weight: 500;">{content}</a>'
        
        tasks_with_date_html_rows += f'''        <tr class="{priority_class}">
          <td class="activity-col">{content_html}</td>
          <td class="priority-cell priority-col">{priority_badge_html}</td>
          <td style="text-align: center; font-size: 14px; color: #64748b;">{formatted_date}</td>
          <td class="labels-col">{labels_container}</td>
        </tr>
'''
    
    tasks_with_date_section = f'''
<div class="card" style="background: #f0f9ff; border-left: 4px solid #3b82f6;">
  <div class="section-title" style="color: #1e40af;">📅 Tareas con Fecha ({len(tasks_with_date)})</div>
  <p class="subtext" style="margin-bottom: 16px; color: #1e3a8a;">Tareas no recurrentes con fecha futura (ordenadas cronológicamente):</p>
  <table>
    <thead>
      <tr><th>Actividad</th><th>P</th><th>Fecha</th><th>Etiquetas</th></tr>
    </thead>
    <tbody>
{tasks_with_date_html_rows}    </tbody>
  </table>
</div>
'''
else:
    tasks_with_date_section = ''

full_html = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Cronograma V7.5 - Morning Alternation Rule (Fixed)</title>
<style>
  /* Dashboard Modular Profesional - Fintech Moderna */
  body {{ 
    font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif; 
    background: #f5f7fa; 
    color: #1f2937; 
    margin: 0; 
    padding: 24px; 
  }}
  
  .card {{
    background: #ffffff;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  }}
  
  .section-title {{
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 12px;
    color: #1f2937;
  }}
  
  .subtext {{
    font-size: 14px;
    color: #6b7280;
  }}
  
  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }}
  
  .grid-3 {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
  }}
  
  .metric {{
    font-size: 28px;
    font-weight: 700;
    color: #111827;
  }}
  
  .progress-bar-bg {{
    background: #e5e7eb;
    height: 8px;
    border-radius: 8px;
    overflow: hidden;
  }}
  
  .progress-bar-fill {{
    height: 100%;
    background: #6366f1;
    border-radius: 8px;
  }}
  /* Tabla dentro de card */
  table {{ 
    border-collapse: separate;
    border-spacing: 0;
    width: 100%; 
    background: white; 
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }}
  thead {{ 
    background: #6366f1; 
    color: white; 
  }}
  th {{ 
    border: none;
    border-bottom: 2px solid #e5e7eb;
    padding: 12px 16px; 
    vertical-align: middle; 
    text-align: left; 
    font-size: 14px;
    font-weight: 600;
  }}
  thead tr:first-child th:first-child {{
    border-top-left-radius: 12px;
  }}
  thead tr:first-child th:last-child {{
    border-top-right-radius: 12px;
  }}
  tbody tr:last-child td:first-child {{
    border-bottom-left-radius: 12px;
  }}
  tbody tr:last-child td:last-child {{
    border-bottom-right-radius: 12px;
  }}
  td {{ 
    border: none;
    border-bottom: 1px solid #f3f4f6;
    padding: 12px 16px; 
    vertical-align: middle; 
    text-align: left; 
    overflow: hidden; 
    line-height: 1.5; 
  }}
  tr {{ background: transparent; }}
  tr:nth-child(even) {{ background: transparent; }}
  tr:hover {{ background: transparent; }}
  a {{ color: #374151; text-decoration: none; }}
  a:hover {{ text-decoration: underline; color: #1f2937; }}
  
  /* --- Label Chips (Moderno) --- */
  .label {{ 
    display: inline-block;
    background: #e5e7eb; 
    color: #374151; 
    padding: 4px 10px; 
    border-radius: 12px; 
    font-size: 11px; 
    margin: 2px 4px 2px 0;
    white-space: nowrap;
    font-weight: 500;
  }}
  
  /* --- Proportional Row Heights (strict) --- */
  .h-5 {{ height: 28px; max-height: 28px; background-color: transparent !important; }}
  .h-5 td {{ padding: 3px 8px; font-size: 16px; line-height: 1.2; background-color: transparent !important; }}
  .h-5:hover {{ background-color: transparent !important; }}
  .h-5:hover td {{ background-color: transparent !important; }}
  
  .h-10 {{ height: 36px; max-height: 36px; background-color: transparent !important; }}
  .h-10 td {{ padding: 4px 10px; font-size: 16px; line-height: 1.3; background-color: transparent !important; }}
  .h-10:hover {{ background-color: transparent !important; }}
  .h-10:hover td {{ background-color: transparent !important; }}
  
  .h-15 {{ height: 44px; max-height: 44px; background-color: transparent !important; }}
  .h-15 td {{ padding: 5px 10px; font-size: 17px; line-height: 1.3; background-color: transparent !important; }}
  
  .h-20 {{ height: 52px; max-height: 52px; background-color: transparent !important; }}
  .h-20 td {{ padding: 6px 12px; font-size: 17px; line-height: 1.4; background-color: transparent !important; }}
  
  .h-30 {{ height: 68px; max-height: 68px; background-color: transparent !important; }}
  .h-30 td {{ padding: 8px 12px; font-size: 18px; line-height: 1.4; background-color: transparent !important; }}
  
  /* Highlight rows with check/checks label */
  tr.has-check-label {{ background-color: #fffdf5 !important; }}
  tr.has-check-label td {{ background-color: #fffdf5 !important; }}
  
  .h-60 {{ height: 100px; max-height: 100px; background-color: transparent !important; }}
  .h-60 td {{ padding: 10px 14px; font-size: 18px; line-height: 1.5; background-color: transparent !important; }}
  
  /* --- Column-specific styles --- */
  .time-col {{ white-space: nowrap; width: 140px; font-size: 16px; text-align: center; background-color: transparent !important; }}
  .time-badge {{
    display: inline-block;
    background: transparent;
    color: #6b7280;
    padding: 6px 12px;
    border-radius: 16px;
    font-weight: 600;
    box-shadow: none;
  }}
  .time-start {{ font-size: 14px; font-weight: 600; }}
  .time-separator {{ font-size: 14px; margin: 0 3px; opacity: 0.8; }}
  .time-end {{ font-size: 12px; opacity: 0.9; }}
  .activity-col {{ max-width: 600px; background-color: transparent !important; color: #374151; }}
  .priority-col {{ width: 45px; text-align: center; padding: 4px !important; background-color: transparent !important; }}
  .duration-col {{ width: 100px; text-align: center; background-color: transparent !important; }}
  .duration-badge {{
    display: inline-block;
    background: transparent;
    color: #6b7280;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    box-shadow: none;
  }}
  .labels-col {{ 
    max-width: 300px; 
    padding: 6px 10px !important;
    vertical-align: middle;
    background-color: white !important;
  }}
  
  /* --- Text Truncation with Tooltip --- */
  .truncate {{ 
    max-width: 400px; 
    white-space: nowrap; 
    overflow: hidden; 
    text-overflow: ellipsis; 
    position: relative;
    display: inline-block;
    vertical-align: middle;
  }}
  
  .truncate:hover::after {{
    content: attr(data-full-text);
    position: absolute;
    left: 0;
    top: 100%;
    background: #2d3748;
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    white-space: normal;
    max-width: 400px;
    width: max-content;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    font-size: 13px;
    line-height: 1.4;
    margin-top: 4px;
  }}
  
  /* --- Type Colors (Background) --- */
  .type-Física {{ background-color: transparent !important; }} .type-Intelectual {{ background-color: transparent !important; }} .type-Administrativa {{ background-color: transparent !important; }} .type-Fija {{ background-color: transparent !important; }} .type-General {{ background-color: transparent !important; }}

  /* --- Priority Colors (Border) --- */
  .priority-p1 {{ border-left: 5px solid #e53e3e; }} .priority-p2 {{ border-left: 5px solid #dd6b20; }} .priority-p3 {{ border-left: 5px solid #3182ce; }} .priority-p4 {{ border-left: 2px solid #a0aec0; }} .priority-p- {{ border-left: 2px solid #a0aec0; }}

  /* --- Priority Cell (Background) --- */
  .priority-cell {{ 
    text-align: center; 
    padding: 6px 4px !important;
    background-color: white !important;
  }}
  
  /* --- Priority Chips (Badge Style) --- */
  .priority-badge {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
  }}
  
  .priority-badge.p1 {{ background-color: #ef4444; color: white; }}
  .priority-badge.p2 {{ background-color: #f59e0b; color: white; }}
  .priority-badge.p3 {{ background-color: #6366f1; color: white; }}
  .priority-badge.p4 {{ background-color: #e5e7eb; color: #6b7280; }}
  
  /* --- Labels Container --- */
  .labels-container {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    align-items: center;
    line-height: 1.6;
  }}
  
  /* --- Legend Styles --- */
  .legend {{
    background: white;
    padding: 20px;
    margin: 20px auto;
    max-width: 1200px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }}
  
  .legend h2 {{
    margin: 0 0 15px 0;
    color: #2d3748;
    font-size: 21px;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 10px;
  }}
  
  .legend-section {{
    margin-bottom: 20px;
  }}
  
  .legend-section h3 {{
    margin: 0 0 10px 0;
    color: #4a5568;
    font-size: 18px;
    font-weight: 600;
  }}
  
  .legend-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 12px;
  }}
  
  .legend-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 16px;
    padding: 6px;
  }}
  
  .legend-emoji {{
    font-size: 22px;
    width: 32px;
    text-align: center;
  }}
  
  .legend-color-box {{
    width: 30px;
    height: 30px;
    border-radius: 4px;
    border: 1px solid #cbd5e0;
  }}

  /* Tareas completadas */
  .completed-task {{
    opacity: 0.6;
    background-color: #f3f4f6 !important;
  }}
  
  .completed-task .activity-col a {{
    text-decoration: line-through;
    color: #6b7280 !important;
  }}
  
  .completed-task .priority-badge {{
    opacity: 0.5;
  }}
  
  .completed-task .label {{
    opacity: 0.5;
  }}
  
  .completed-task input[type="checkbox"]:checked {{
    cursor: not-allowed;
  }}
</style>
</head>
<body>
<div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
  <h1 style="margin: 0; font-size: 24px; font-weight: 700;">✅ Cronograma V7.5 - Regla de Alternancia Matinal (Corregida)</h1>
  <p style="margin: 12px 0 16px 0; opacity: 0.95; font-size: 14px;">
    <strong>Fecha:</strong> {target_date.strftime("%d/%m/%Y")} (Generado: {datetime.now().strftime("%H:%M:%S")})<br>
    <strong>Estrategia:</strong> No permite dos tareas físicas seguidas en la mañana. Debe ser 1 intelectual + 1 física, o 2 intelectuales + 1 física.
  </p>
  <div style="display: flex; gap: 15px; flex-wrap: wrap; justify-content: center;">
    <button onclick="regenerarCronograma()" style="
      background: white;
      color: #667eea;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      transition: all 0.3s ease;
      flex: 1;
      min-width: 200px;
      max-width: 300px;
    " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
      🔄 Regenerar Cronograma
    </button>
    <a href="/cronograma/manana" style="
      background: white;
      color: #667eea;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      font-size: 16px;
      font-weight: 600;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      transition: all 0.3s ease;
      flex: 1;
      min-width: 200px;
      max-width: 300px;
      text-decoration: none;
      display: flex;
      align-items: center;
      justify-content: center;
    " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
      👁️ Ver Cronograma de Mañana
    </a>
  </div>
</div>

<!-- IDEALISTA STATISTICS SECTION -->
{idealista_section}

<!-- FIREFLY III STATISTICS SECTION -->
{firefly_section}

<!-- NEW EVENTS SECTION -->
{new_events_section}

<div class="card">
  <div class="section-title">Cronograma del Día</div>
  <table>
    <thead>
      <tr><th>✓</th><th>Hora</th><th>Actividad</th><th>P</th><th>Duración</th><th>Etiquetas</th></tr>
    </thead>
    <tbody>
      {html_rows}
    </tbody>
  </table>
</div>

<!-- TASKS WITH DATE SECTION -->
{tasks_with_date_section}

<!-- UNASSIGNED TASKS SECTION -->
{unassigned_tasks_section}

<!-- WEEKLY CALENDAR SECTION -->
<div style="margin-top: 40px; padding: 20px; background: white; border-left: 5px solid #667eea; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <h2 style="margin: 0 0 20px 0; color: #5a67d8; font-size: 24px; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">📅 Calendario Semanal</h2>
  <div id="weekly-calendar" style="overflow-x: auto;">
    <div style="text-align: center; padding: 40px; color: #a0aec0;">
      <p style="margin: 0; font-size: 16px;">Cargando calendario...</p>
    </div>
  </div>
</div>

<style>
  .modern-week-calendar {{
    width: 100%;
    padding: 15px;
    border-radius: 10px;
    background: #fafbfc;
  }}
  
  .global-header {{
    display: flex;
    margin-bottom: 0;
  }}
  
  .global-header-day-space {{
    width: 90px;
    background: #8b9dc3;
    border-radius: 6px 0 0 0;
  }}
  
  .global-header-hours {{
    flex: 1;
    display: flex;
    overflow: hidden;
  }}
  
  .global-hour-label {{
    flex: 1;
    padding: 10px 3px;
    text-align: center;
    font-weight: 600;
    font-size: 10px;
    color: white;
    background: #8b9dc3;
    border-right: 1px solid #6b7fa3;
  }}
  
  .global-hour-label:last-child {{
    border-radius: 0 6px 0 0;
  }}
  
  .modern-day-row {{
    margin-bottom: 3px;
    display: flex;
    align-items: stretch;
    border-radius: 6px;
    overflow: visible;
    background: #f9fafb;
  }}
  
  .modern-day-row.today-row {{
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    border: 1px solid #e5e7eb;
  }}
  
  .modern-day-row.weekend {{
    background: #f0f9f6;
  }}
  
  .modern-day-label {{
    background: #a8b5cc;
    color: white;
    padding: 10px 8px;
    font-weight: 700;
    font-size: 12px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 90px;
    border-radius: 6px 0 0 6px;
  }}
  
  .modern-day-row.weekend .modern-day-label {{
    background: #6fb3a0;
  }}
  
  .modern-timeline-container {{
    flex: 1;
    position: relative;
    overflow: visible;
  }}
  
  .modern-timeline-body {{
    position: relative;
    height: 60px;
    display: flex;
  }}
  
  .modern-hour-cell {{
    flex: 1;
    position: relative;
    border: 1px solid #e8e8e8;
    margin: 2px;
    border-radius: 6px;
  }}
  
  .modern-event-bar {{
    position: absolute;
    background: white;
    border-left: 4px solid #667eea;
    color: #555;
    padding: 6px 8px;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 600;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    display: flex;
    align-items: center;
    top: 10px;
    height: 40px;
    z-index: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    transition: all 0.2s;
  }}
  
  .modern-event-bar:hover {{
    z-index: 100;
    transform: scale(1.08);
    box-shadow: 0 3px 8px rgba(0,0,0,0.15);
    overflow: visible;
    white-space: normal;
  }}
</style>

<script>
// Regenerar cronograma
async function regenerarCronograma() {{
  const button = event.target;
  const originalText = button.innerHTML;
  button.innerHTML = '⏳ Regenerando...';
  button.disabled = true;
  
  try {{
    const response = await fetch('/regenerate', {{
      method: 'POST'
    }});
    const data = await response.json();
    
    if (data.success) {{
      button.innerHTML = '✅ ¡Listo!';
      setTimeout(() => {{
        window.location.reload(true); // Force reload without cache
      }}, 500);
    }} else {{
      button.innerHTML = '❌ Error';
      alert('Error al regenerar: ' + (data.error || 'Desconocido'));
      setTimeout(() => {{
        button.innerHTML = originalText;
        button.disabled = false;
      }}, 2000);
    }}
  }} catch (error) {{
    console.error('Error:', error);
    button.innerHTML = '❌ Error';
    alert('Error al regenerar el cronograma');
    setTimeout(() => {{
      button.innerHTML = originalText;
      button.disabled = false;
    }}, 2000);
  }}
}}

// Fetch and display weekly calendar
async function loadWeeklyCalendar() {{
  try {{
    const response = await fetch('/week-calendar');
    const data = await response.json();
    
    if (!data.success) {{
      console.error('Error loading calendar:', data);
      return;
    }}
    
    const calendarContainer = document.getElementById('weekly-calendar');
    
    // Get today's date and next 6 days
    const today = new Date();
    const daysOfWeek = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    
    // Create modern grid calendar
    let html = '<div class="modern-week-calendar">';
    
    // Global header with hours (only once)
    html += '<div class="global-header">';
    html += '<div class="global-header-day-space"></div>';
    html += '<div class="global-header-hours">';
    for (let hour = 8; hour <= 21; hour++) {{
      html += `<div class="global-hour-label">${{hour}}</div>`;
    }}
    html += '</div></div>';
    
    // Create rows for each day (7 days)
    const dates = [];
    for (let i = 0; i < 7; i++) {{
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      dates.push(date);
    }}
    
    // Create one row per day
    for (let dayIndex = 0; dayIndex < 7; dayIndex++) {{
      const date = dates[dayIndex];
      const dateKey = date.toISOString().split('T')[0];
      const dayName = daysOfWeek[date.getDay()];
      const isToday = dayIndex === 0;
      const isWeekend = date.getDay() === 0 || date.getDay() === 6;
      const events = data.events[dateKey] || [];
      
      // Day row
      html += `<div class="modern-day-row ${{isToday ? 'today-row' : ''}} ${{isWeekend ? 'weekend' : ''}}">`;  
      html += `<div class="modern-day-label">${{dayName}}</div>`;
      
      // Timeline container
      html += '<div class="modern-timeline-container">';
      html += '<div class="modern-timeline-body">';
      
      // Hour cells
      for (let hour = 8; hour <= 21; hour++) {{
        html += '<div class="modern-hour-cell"></div>';
      }}
      
      // Events positioned absolutely
      const eventColors = ['#667eea', '#f5576c', '#00d4ff', '#38f9d7', '#ffa502', '#ff6348', '#5f27cd', '#00b894'];
      events.forEach((event, index) => {{
        if (!event.all_day) {{
          const [startHour, startMinute] = event.start.split(':').map(Number);
          const [endHour, endMinute] = event.end.split(':').map(Number);
          
          // Calculate position and width
          const startOffset = (startHour - 8) + (startMinute / 60);
          const duration = (endHour * 60 + endMinute) - (startHour * 60 + startMinute);
          const durationHours = duration / 60;
          const durationText = duration >= 60 ? `${{Math.floor(duration/60)}}h` : `${{duration}}m`;
          
          // Calculate position and width as percentage
          const totalHours = 14; // 8 to 21 = 14 hours
          const leftPercent = (startOffset / totalHours) * 100;
          const widthPercent = (durationHours / totalHours) * 100;
          const color = eventColors[index % eventColors.length];
          
          html += `<div class="modern-event-bar" style="left: ${{leftPercent}}%; width: ${{widthPercent}}%; border-left-color: ${{color}};" title="${{event.summary}} (${{event.start}} - ${{event.end}})">${{event.summary}}</div>`;
        }}
      }});
      
      html += '</div></div></div>';
    }}
    
    html += '</div>';
    
    calendarContainer.innerHTML = html;
    
  }} catch (error) {{
    console.error('Error loading weekly calendar:', error);
    document.getElementById('weekly-calendar').innerHTML = `
      <div style="text-align: center; padding: 40px; color: #e53e3e;">
        <p style="margin: 0; font-size: 16px;">❌ Error al cargar el calendario</p>
      </div>
    `;
  }}
}}

// Load calendar when page loads
window.addEventListener('DOMContentLoaded', loadWeeklyCalendar);

// Handle task completion checkboxes
document.addEventListener('DOMContentLoaded', function() {{
    const checkboxes = document.querySelectorAll('.task-checkbox');
    
    checkboxes.forEach(checkbox => {{
        checkbox.addEventListener('change', async function() {{
            if (this.checked) {{
                const taskId = this.getAttribute('data-task-id');
                const content = this.getAttribute('data-content');
                const startTime = this.getAttribute('data-start-time');
                const endTime = this.getAttribute('data-end-time');
                const priority = this.getAttribute('data-priority');
                const labelsStr = this.getAttribute('data-labels');
                const labels = labelsStr ? JSON.parse(labelsStr) : [];
                
                const row = this.closest('tr');
                
                // FASE 1: Mark row as completed visually IMMEDIATELY
                row.style.transition = 'all 0.3s ease';
                row.style.backgroundColor = '#f3f4f6';
                row.style.opacity = '0.6';
                
                // Keep checkbox checked and disabled
                this.checked = true;
                this.disabled = true;
                
                try {{
                    const response = await fetch('/complete-task', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{
                            task_id: taskId,
                            content: content,
                            start_time: startTime,
                            end_time: endTime,
                            priority: priority,
                            labels: labels
                        }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        // Task completed and saved locally
                        console.log('✅ Tarea completada y guardada localmente');
                        // NO reload - keep the visual mark
                    }} else {{
                        alert('❌ Error al completar la tarea: ' + (data.error || 'Error desconocido'));
                        // Revert visual changes on error
                        row.style.backgroundColor = '';
                        row.style.opacity = '';
                        this.checked = false;
                        this.disabled = false;
                    }}
                }} catch (error) {{
                    alert('❌ Error de conexión: ' + error.message);
                    // Revert visual changes on error
                    row.style.backgroundColor = '';
                    row.style.opacity = '';
                    row.style.textDecoration = '';
                    this.checked = false;
                    this.disabled = false;
                }}
            }}
        }});
    }});
}});
</script>

</body>
</html>'''

import os
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
base_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(base_dir, f"cronograma_v7_5_{timestamp}.html")
with open(output_file, "w", encoding="utf-8") as f:
    f.write(full_html)

print(f"\n✅ Cronograma V7.5 guardado en:")
print(f"   {output_file}")

# --- Generate ICS (iCalendar) file ---

print("\n6️⃣ Generating ICS file for calendar import...")

ics_exporter = ICSExporter()

# Add all events to ICS
for task in final_cronograma:
    ics_exporter.add_event(
        title=task.get("content", "Sin título"),
        start_time=task.get("start_time", "00:00"),
        end_time=task.get("end_time", "00:00"),
        description=" ".join(task.get("labels", [])),
        priority=task.get("priority", "P4"),
        task_type=task.get("type", "General"),
        url=task.get("url", "")
    )

# Save ICS file with target date
target_date_str = target_date.strftime("%Y-%m-%d")
ics_output_file = os.path.join(base_dir, f"cronograma_v7_5_{timestamp}.ics")
ics_exporter.save_to_file(ics_output_file, date=target_date_str)

print(f"\n✅ Archivo ICS guardado en:")
print(f"   {ics_output_file}")
print("\n" + "="*80)
print("✅ ¡ÉXITO! CRONOGRAMA V7.5 CON REGLA DE ALTERNANCIA MATINAL CORREGIDA")
print("✅ Archivos generados: HTML + ICS (importable a Google Calendar)")
print("="*80)
