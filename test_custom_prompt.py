"""
Test script with custom user-defined prompt
Using Manus integrated OpenAI API for testing
"""

from openai import OpenAI
from config import get_config
from todoist_client import TodoistClient
from datetime import datetime

# Use Manus integrated OpenAI API for testing
client = OpenAI()

config = get_config()

print("="*80)
print("📅 TESTING CUSTOM PROMPT WITH YOUR RULES")
print("="*80)

# Get real tasks from Todoist
print("\n1️⃣ Fetching tasks from Todoist...")
todoist_client = TodoistClient(config['TODOIST_API_TOKEN'])
all_tasks = todoist_client.get_today_tasks()
formatted_tasks = todoist_client.format_tasks_for_display(all_tasks)
print(f"✅ Found {len(formatted_tasks)} tasks for today")

# Sample calendar events
calendar_events = [
    {
        "title": "Reunión de equipo",
        "start_time": "10:00",
        "end_time": "11:00",
        "location": "Oficina"
    },
    {
        "title": "Llamada con cliente",
        "start_time": "16:00",
        "end_time": "16:30",
        "location": ""
    }
]
print(f"✅ Using {len(calendar_events)} sample calendar events")

# Prepare data in JSON format
data_json = {
    "eventos_calendario": calendar_events,
    "tareas_todoist": formatted_tasks
}

# Build custom prompt
prompt = f"""Genera el cronograma del día siguiendo estas instrucciones OBLIGATORIAS:

1. Respeta EXACTAMENTE los eventos del calendario: no modificarlos, no moverlos.

2. Coloca las tareas de Todoist en los huecos disponibles entre eventos.

3. Cada tarea ocupa su duración si la tiene; si no, asigna 20 minutos.

4. Organiza todo en bloques de 20 minutos (subdivisiones de 10 o 5 solo si es necesario).

5. Alterna tareas intelectuales y físicas/administrativas (según etiquetas en el JSON o inferencia por contenido).

6. No más de dos tareas intelectuales seguidas.

7. Las llamadas y gestiones cortas → al final de la mañana siempre que sea posible.

8. Si una tarea no cabe, no la pierdas. Añade al final una segunda tabla llamada: "Pendientes no asignadas".

9. No devuelvas nada más que las tablas.

10. Reserva SIEMPRE un bloque fijo de 14:00–15:00 para "Comer".
    - Es un evento fijo del día.
    - No puede ser movido ni sustituido.

11. Añade SIEMPRE la tarea "Desayunar" de 20 minutos, aunque no aparezca en el JSON.
    - Debe colocarse en el primer hueco disponible de la mañana, antes del primer evento o tarea.
    - Tipo = "Tarea fija".

12. El día empieza a las 07:00 y termina a las 21:00.
    - Solo puedes utilizar ese intervalo para organizar tareas y eventos.
    - Nada puede colocarse antes de las 07:00 ni después de las 21:00.

DATOS DEL DÍA:

```json
{str(data_json)}
```

FORMATO DE SALIDA:

Devuelve SOLO código HTML con:
1. Una tabla principal con el cronograma del día (07:00 a 21:00)
2. Si es necesario, una segunda tabla con "Pendientes no asignadas"

Columnas de la tabla:
- Hora (formato HH:MM - HH:MM)
- Actividad
- Tipo (Evento / Tarea / Tarea fija)
- Etiquetas (si las tiene)
- Duración

Usa estilos CSS inline para que se vea profesional en email.
Usa colores para diferenciar tipos de actividades.
"""

print("\n2️⃣ Sending to ChatGPT with custom prompt...")
print("   (This may take 20-30 seconds...)")

try:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente experto en organización de tiempo y productividad. Sigues las instrucciones al pie de la letra y generas cronogramas optimizados."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=3000
    )
    
    agenda_html = response.choices[0].message.content
    
    print("✅ ChatGPT response received!")
    print(f"   HTML length: {len(agenda_html)} characters")
    
    # Save to file
    output_file = f"/home/ubuntu/daily-agenda-automation/cronograma_custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(agenda_html)
    
    print(f"\n✅ Cronograma saved to: {output_file}")
    print("\n" + "="*80)
    print("✅ SUCCESS! CUSTOM PROMPT WORKING!")
    print("="*80)
    print(f"\nYou can view the generated cronograma at:")
    print(f"  {output_file}")
    
    # Show preview
    print("\n📋 Preview of generated content:")
    print(agenda_html[:800] + "..." if len(agenda_html) > 800 else agenda_html)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
