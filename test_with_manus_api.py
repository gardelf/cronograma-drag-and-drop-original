"""
Test script using Manus integrated OpenAI API
"""

from openai import OpenAI
import os
from config import get_config
from todoist_client import TodoistClient

# Use Manus integrated OpenAI API
client = OpenAI()  # Uses OPENAI_API_KEY from environment (Manus provides this)

config = get_config()

print("="*60)
print("📅 TESTING WITH MANUS INTEGRATED OPENAI API")
print("="*60)

# Get tasks from Todoist
print("\n1️⃣ Fetching tasks from Todoist...")
todoist_client = TodoistClient(config['TODOIST_API_TOKEN'])
tasks = todoist_client.get_today_tasks()
formatted_tasks = todoist_client.format_tasks_for_display(tasks)
print(f"✅ Found {len(formatted_tasks)} tasks")

# Sample calendar events
calendar_events = [
    {"title": "Reunión de equipo", "start_time": "10:00", "location": "Oficina"},
    {"title": "Comida", "start_time": "14:00", "location": "Restaurante"}
]
print(f"✅ Using {len(calendar_events)} sample calendar events")

# Build prompt
prompt = f"""Tengo los siguientes eventos de calendario y tareas pendientes para hoy. 
Organízalos en una tabla HTML profesional y bien estructurada.

FORMATO DE LA TABLA:
- Usa HTML con estilos CSS inline
- Columnas: Hora | Actividad | Tipo | Prioridad | Duración Estimada
- Ordena cronológicamente
- Usa colores: 
  * #ff4444 (rojo) para prioridad Urgente
  * #ff8800 (naranja) para prioridad Alta
  * #ffcc00 (amarillo) para prioridad Media
  * #44ff44 (verde) para prioridad Baja
- Incluye un título "📅 Agenda del Día - {os.popen('date +"%d/%m/%Y"').read().strip()}"
- Haz la tabla responsive y profesional
- Añade un footer con el total de actividades

📅 EVENTOS DEL CALENDARIO:
"""

for event in calendar_events:
    prompt += f"- {event['start_time']}: {event['title']}"
    if event.get('location'):
        prompt += f" (Ubicación: {event['location']})"
    prompt += "\n"

prompt += "\n✅ TAREAS PENDIENTES DE TODOIST:\n"
for task in formatted_tasks:
    prompt += f"- {task['content']}"
    if task.get('due_time'):
        prompt += f" (Hora: {task['due_time']})"
    prompt += f" [Prioridad: {task['priority']}]"
    if task.get('labels'):
        prompt += f" {task['labels']}"
    prompt += "\n"

prompt += """
Devuelve SOLO el código HTML completo de la tabla, sin explicaciones adicionales.
La tabla debe ser completa, profesional y lista para enviar por email.
Incluye estilos CSS inline para que se vea bien en cualquier cliente de email.
"""

print("\n2️⃣ Sending to ChatGPT...")
print("   (This may take 10-20 seconds...)")

try:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",  # Using Manus optimized model
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente de productividad experto. Creas tablas HTML profesionales y bien formateadas."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    agenda_html = response.choices[0].message.content
    
    print("✅ ChatGPT response received!")
    print(f"   HTML length: {len(agenda_html)} characters")
    
    # Save to file
    from datetime import datetime
    output_file = f"/home/ubuntu/daily-agenda-automation/agenda_chatgpt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(agenda_html)
    
    print(f"\n✅ Agenda saved to: {output_file}")
    print("\n" + "="*60)
    print("✅ SUCCESS! ChatGPT INTEGRATION WORKING!")
    print("="*60)
    print(f"\nYou can view the generated agenda at:")
    print(f"  {output_file}")
    
    # Show preview
    print("\n📋 Preview of generated content:")
    print(agenda_html[:500] + "..." if len(agenda_html) > 500 else agenda_html)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
