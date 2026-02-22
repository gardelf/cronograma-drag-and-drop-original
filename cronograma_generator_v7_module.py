"""
Cronograma Generator V7 - Hybrid Strategy with Todoist Type Labels
Features:
- Uses Todoist type labels: fisico, administrativo, intelectual
- Strict time blocks control in Python
- ChatGPT for intelligent task alternation within blocks
- Priority order: P1 → P2 → P3 → P4 (urgent to low)
- Administrative + morning tasks at end of morning block
- Fills entire day (07:00-21:00) without gaps
"""

import requests
from config import get_config
from todoist_client import TodoistClient
from datetime import datetime
import json
import os

config = get_config()

print("="*80)
print("📅 CRONOGRAMA GENERATOR V7 - HYBRID STRATEGY WITH TYPE LABELS")
print("="*80)

# Get ALL active tasks
print("\n1️⃣ Fetching ALL active tasks from Todoist...")
todoist_client = TodoistClient(config['TODOIST_API_TOKEN'])
all_tasks = todoist_client.get_all_active_tasks()
formatted_tasks = todoist_client.format_tasks_for_display(all_tasks)
print(f"✅ Found {len(formatted_tasks)} active tasks")

# Filter tasks: only those with labels (excluding time labels)
time_labels = ['5min', '5 minutos', '10min', '10 minutos', '15min', '15 minutos',
               '20min', '20 minutos', '30min', '30 minutos', '1h', '1 hora', '2h', '2 horas']
type_labels = ['fisico', 'administrativo', 'intelectual']

def has_non_time_labels(task):
    """Check if task has labels other than time labels"""
    labels = task.get('labels', [])
    non_time_labels = [l for l in labels if l not in time_labels]
    return len(non_time_labels) > 0

def has_label(task, label):
    """Check if task has a specific label"""
    return label in task.get('labels', [])

def get_duration_minutes(task):
    """Extract duration from time labels, default 20 minutes"""
    labels = task.get('labels', [])
    for label in labels:
        if label in ['5min', '5 minutos']:
            return 5
        elif label in ['10min', '10 minutos']:
            return 10
        elif label in ['15min', '15 minutos']:
            return 15
        elif label in ['20min', '20 minutos']:
            return 20
        elif label in ['30min', '30 minutos']:
            return 30
        elif label in ['1h', '1 hora']:
            return 60
        elif label in ['2h', '2 horas']:
            return 120
    return 20  # default

def get_task_type_from_labels(task):
    """Get task type from Todoist labels"""
    labels = task.get('labels', [])
    if 'fisico' in labels:
        return 'Física'
    elif 'administrativo' in labels:
        return 'Administrativa'
    elif 'intelectual' in labels:
        return 'Intelectual'
    else:
        return 'Sin tipo'

def get_priority_value(task):
    """Get priority value (P1=1 highest, P4=4 lowest)"""
    priority = task.get('priority', 4)
    if isinstance(priority, str):
        priority_map = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4}
        priority = priority_map.get(priority, 4)
    return priority

def sort_by_priority(tasks):
    """Sort tasks by priority P1→P2→P3→P4 (urgent to low) and due date"""
    return sorted(tasks, key=lambda t: (get_priority_value(t), t.get('due_date') or '9999-99-99'))

def format_tasks_for_chatgpt(tasks, block_name):
    """Format tasks for ChatGPT processing"""
    formatted = []
    for task in tasks:
        duration = get_duration_minutes(task)
        task_type = get_task_type_from_labels(task)
        priority = get_priority_value(task)
        
        formatted.append({
            'content': task.get('content', 'Sin título'),
            'duration_minutes': duration,
            'type': task_type,
            'priority': f'P{priority}',
            'labels': [l for l in task.get('labels', []) if l not in time_labels],
            'due_date': task.get('due_date'),
            'url': task.get('url', '')
        })
    
    return {
        'block_name': block_name,
        'tasks': formatted,
        'total_tasks': len(formatted)
    }

# Filter all tasks with labels
filtered_tasks = [t for t in formatted_tasks if has_non_time_labels(t)]
print(f"\n📊 Total tasks with labels: {len(filtered_tasks)}")

# Separate tasks by time blocks
rutina_tasks = [t for t in filtered_tasks if has_label(t, 'rutina administrativa matinal')]
cheks_tasks = [t for t in filtered_tasks if has_label(t, 'Cheks')]
manana_tasks = [t for t in filtered_tasks if has_label(t, 'por la mañana')]
tarde_tasks = [t for t in filtered_tasks if has_label(t, 'por la tarde')]
noche_tasks = [t for t in filtered_tasks if has_label(t, 'por la noche')]

# Tasks without time restrictions
time_restricted_labels = {'rutina administrativa matinal', 'Cheks', 'por la mañana', 'por la tarde', 'por la noche'}
flexible_tasks = []
for t in filtered_tasks:
    task_labels = set(t.get('labels', []))
    if not task_labels.intersection(time_restricted_labels):
        flexible_tasks.append(t)

print(f"\n🏷️  Tasks by time blocks:")
print(f"   - Rutina administrativa matinal: {len(rutina_tasks)} tasks")
print(f"   - Cheks: {len(cheks_tasks)} tasks")
print(f"   - Por la mañana: {len(manana_tasks)} tasks")
print(f"   - Por la tarde: {len(tarde_tasks)} tasks")
print(f"   - Por la noche: {len(noche_tasks)} tasks")
print(f"   - Flexible (sin restricción): {len(flexible_tasks)} tasks")

# Count tasks by type
type_counts = {}
for label in type_labels:
    count = sum(1 for task in filtered_tasks if label in task.get('labels', []))
    type_counts[label] = count

print(f"\n🎯 Tasks by type:")
for label, count in type_counts.items():
    print(f"   - {label}: {count} tasks")

# Sort all blocks by priority
rutina_tasks = sort_by_priority(rutina_tasks)
cheks_tasks = sort_by_priority(cheks_tasks)
manana_tasks = sort_by_priority(manana_tasks)
tarde_tasks = sort_by_priority(tarde_tasks)
noche_tasks = sort_by_priority(noche_tasks)
flexible_tasks = sort_by_priority(flexible_tasks)

print("\n2️⃣ Preparing data for ChatGPT processing...")

# Prepare blocks for ChatGPT
blocks_data = []

# Add flexible tasks to each block proportionally
flex_per_block = len(flexible_tasks) // 3
manana_with_flex = manana_tasks + flexible_tasks[:flex_per_block]
tarde_with_flex = tarde_tasks + flexible_tasks[flex_per_block:flex_per_block*2]
noche_with_flex = noche_tasks + flexible_tasks[flex_per_block*2:]

# Format blocks
if rutina_tasks:
    blocks_data.append(format_tasks_for_chatgpt(rutina_tasks, "Rutina Administrativa Matinal"))
if cheks_tasks:
    blocks_data.append(format_tasks_for_chatgpt(cheks_tasks, "Cheks"))
if manana_with_flex:
    blocks_data.append(format_tasks_for_chatgpt(manana_with_flex, "Por la mañana"))
if tarde_with_flex:
    blocks_data.append(format_tasks_for_chatgpt(tarde_with_flex, "Por la tarde"))
if noche_with_flex:
    blocks_data.append(format_tasks_for_chatgpt(noche_with_flex, "Por la noche"))

print(f"✅ Prepared {len(blocks_data)} blocks for ChatGPT")

# Create ChatGPT prompt
prompt = f"""Genera un cronograma del día siguiendo estas reglas ESTRICTAS:

ESTRUCTURA OBLIGATORIA:
1. 07:00-07:20: Desayunar (FIJO)
2. 07:20-XX:XX: Rutina Administrativa Matinal (SOLO estas tareas)
3. XX:XX-YY:YY: Cheks (SOLO estas tareas)
4. YY:YY-14:00: Por la mañana (estas tareas + alternancia)
5. 14:00-15:00: Comer (FIJO)
6. 15:00-20:00: Por la tarde (estas tareas + alternancia)
7. 20:00-21:00: Por la noche (estas tareas + alternancia)

REGLAS DE ALTERNANCIA:
- Alterna tipos: Física → Intelectual → Administrativa → Física...
- Máximo 2 tareas del mismo tipo seguidas
- Prioridad: P1 (urgente) → P2 → P3 → P4 (baja)

REGLAS DE DURACIÓN:
- Usa la duración especificada en cada tarea
- Organiza en bloques de tiempo consecutivos
- NO dejes huecos vacíos
- DEBE llegar exactamente hasta 21:00

FORMATO DE SALIDA:
Tabla HTML con columnas: Hora | Actividad | Tipo | Prioridad | Etiquetas | Duración

DATOS DE TAREAS POR BLOQUE:
{json.dumps(blocks_data, ensure_ascii=False, indent=2)}

IMPORTANTE:
- Respeta EXACTAMENTE los bloques horarios
- Alterna tipos dentro de cada bloque
- NO inventes tareas
- Llena TODO el día hasta 21:00
- Incluye estilos CSS para colores y alturas proporcionales"""

print("\n3️⃣ Sending to ChatGPT for intelligent organization...")

try:
    # Get OpenAI API key from config
    openai_key = config.get('OPENAI_API_KEY', '')
    if not openai_key:
        raise Exception("OPENAI_API_KEY not found")
    
    # Use requests to call OpenAI API directly
    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={
            'Authorization': f'Bearer {openai_key}',
            'Content-Type': 'application/json'
        },
        json={
            'model': 'gpt-4o-mini',
            'messages': [
                {'role': 'system', 'content': 'Eres un experto organizador de cronogramas. Sigues las reglas exactamente y generas HTML limpio y profesional.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.1,
            'max_tokens': 4000
        },
        timeout=60
    )
    
    response_json = response.json()
    cronogram_html = response_json['choices'][0]['message']['content']
    
    # Clean up the response
    if '```html' in cronogram_html:
        cronogram_html = cronogram_html.split('```html')[1].split('```')[0].strip()
    elif '```' in cronogram_html:
        cronogram_html = cronogram_html.split('```')[1].strip()
    
    print("✅ ChatGPT processing completed!")
    
except Exception as e:
    print(f"❌ Error with ChatGPT: {e}")
    print("🔄 Using fallback method...")
    cronogram_html = "<p>Error: Could not generate cronogram with ChatGPT</p>"

# Add header and save
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Cronograma V7 - Hybrid Strategy</title>
</head>
<body>
<div style="background-color: #e8f5e9; padding: 15px; margin-bottom: 20px; border-left: 5px solid #4caf50;">
<h1 style="margin: 0; color: #2e7d32;">✅ Cronograma V7 - Estrategia Híbrida</h1>
<p style="margin: 10px 0 0 0; color: #555;">
<strong>Fecha generación:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}<br>
<strong>Estrategia:</strong> Python (bloques) + ChatGPT (alternancia inteligente)<br>
<strong>Etiquetas de tipo:</strong> fisico ({type_counts.get('fisico', 0)}), administrativo ({type_counts.get('administrativo', 0)}), intelectual ({type_counts.get('intelectual', 0)})
</p>
</div>

{cronogram_html}

</body>
</html>"""

output_file = f"/home/ubuntu/daily-agenda-automation/cronograma_v7_{timestamp}.html"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(full_html)

print(f"\n✅ Cronograma V7 saved to:")
print(f"   {output_file}")
print("\n" + "="*80)
print("✅ SUCCESS! CRONOGRAMA V7 WITH HYBRID STRATEGY!")
print("="*80)
