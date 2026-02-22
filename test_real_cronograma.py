"""
Generate REAL cronograma with ONLY real Todoist tasks
No fake events, no free time blocks
"""

from openai import OpenAI
from config import get_config
from todoist_client import TodoistClient
from datetime import datetime
import json

# Use Manus integrated OpenAI API
client = OpenAI()

config = get_config()

print("="*80)
print("📅 GENERATING REAL CRONOGRAMA WITH YOUR 73 TODOIST TASKS")
print("="*80)

# Get ALL active tasks from Todoist
print("\n1️⃣ Fetching ALL active tasks from Todoist...")
todoist_client = TodoistClient(config['TODOIST_API_TOKEN'])
all_tasks = todoist_client.get_all_active_tasks()
formatted_tasks = todoist_client.format_tasks_for_display(all_tasks)
print(f"✅ Found {len(formatted_tasks)} active tasks")

# NO calendar events - empty array
calendar_events = []
print("✅ No calendar events (using only Todoist tasks)")

# Prepare data
data_json = {
    "eventos_calendario": calendar_events,
    "tareas_todoist": formatted_tasks
}

# Build custom prompt - MODIFIED to fill the day completely
prompt = f"""Genera el cronograma del día siguiendo estas instrucciones OBLIGATORIAS:

1. NO hay eventos de calendario hoy. Solo organiza las tareas de Todoist.

2. Cada tarea ocupa su duración si la tiene; si no, asigna 20 minutos.

3. Organiza todo en bloques de 20 minutos (subdivisiones de 10 o 5 solo si es necesario).

4. Alterna tareas intelectuales y físicas/administrativas (según etiquetas en el JSON o inferencia por contenido).
   - Etiquetas "motivación", "hábitos" → intelectuales
   - Etiquetas "obligación", "autopromotor" → administrativas/gestión
   - Sin etiqueta → inferir por contenido

5. No más de dos tareas intelectuales seguidas.

6. Las llamadas y gestiones cortas → al final de la mañana siempre que sea posible.

7. LLENA TODO EL DÍA con tareas reales. NO dejes bloques "libres". 
   - Si hay más tareas de las que caben en un día, selecciona las más prioritarias o con fecha de vencimiento más cercana.
   - Organiza tantas tareas como quepan de 07:00 a 21:00.

8. Si quedan tareas sin asignar, añade al final una segunda tabla llamada: "Pendientes no asignadas".

9. No devuelvas nada más que las tablas HTML.

10. Reserva SIEMPRE un bloque fijo de 14:00–15:00 para "Comer".
    - Es un evento fijo del día.
    - No puede ser movido ni sustituido.

11. Añade SIEMPRE la tarea "Desayunar" de 20 minutos al inicio.
    - Debe colocarse a las 07:00-07:20.
    - Tipo = "Tarea fija".

12. El día empieza a las 07:00 y termina a las 21:00.
    - Solo puedes utilizar ese intervalo para organizar tareas.
    - Nada puede colocarse antes de las 07:00 ni después de las 21:00.

13. PRIORIZA tareas con fecha de vencimiento (due_date) más cercana.

14. Muestra las etiquetas de cada tarea en la columna correspondiente.

DATOS DEL DÍA:

```json
{json.dumps(data_json, indent=2, ensure_ascii=False)}
```

FORMATO DE SALIDA:

Devuelve SOLO código HTML con:
1. Una tabla principal con el cronograma del día (07:00 a 21:00) COMPLETAMENTE LLENO de tareas reales
2. Una segunda tabla con "Pendientes no asignadas" (las tareas que no cupieron)

Columnas de la tabla:
- Hora (formato HH:MM - HH:MM)
- Actividad (nombre real de la tarea de Todoist)
- Tipo (Tarea / Tarea fija)
- Etiquetas (mostrar las etiquetas reales de la tarea)
- Duración

Usa estilos CSS inline para que se vea profesional en email.
Usa colores para diferenciar tipos de actividades y etiquetas.
"""

print("\n2️⃣ Sending to ChatGPT with ALL your real tasks...")
print("   (This may take 30-40 seconds due to the large amount of data...)")

try:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente experto en organización de tiempo y productividad. Sigues las instrucciones al pie de la letra y generas cronogramas optimizados usando SOLO datos reales proporcionados."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
        max_tokens=4000
    )
    
    agenda_html = response.choices[0].message.content
    
    print("✅ ChatGPT response received!")
    print(f"   HTML length: {len(agenda_html)} characters")
    
    # Save to file
    output_file = f"/home/ubuntu/daily-agenda-automation/cronograma_real_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(agenda_html)
    
    print(f"\n✅ Real cronograma saved to: {output_file}")
    print("\n" + "="*80)
    print("✅ SUCCESS! REAL CRONOGRAMA WITH YOUR ACTUAL TASKS!")
    print("="*80)
    print(f"\nYou can view the generated cronograma at:")
    print(f"  {output_file}")
    
    # Show preview
    print("\n📋 Preview of generated content:")
    lines = agenda_html.split('\n')
    for i, line in enumerate(lines[:50]):  # Show first 50 lines
        print(line)
    
    if len(lines) > 50:
        print(f"\n... ({len(lines) - 50} more lines)")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
