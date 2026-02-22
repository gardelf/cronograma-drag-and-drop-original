"""
Generate COMPLETE cronograma from 07:00 to 21:00
Force ChatGPT to fill the ENTIRE day
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
print("📅 GENERATING COMPLETE CRONOGRAMA 07:00-21:00")
print("="*80)

# Get ALL active tasks
print("\n1️⃣ Fetching ALL active tasks from Todoist...")
todoist_client = TodoistClient(config['TODOIST_API_TOKEN'])
all_tasks = todoist_client.get_all_active_tasks()
formatted_tasks = todoist_client.format_tasks_for_display(all_tasks)
print(f"✅ Found {len(formatted_tasks)} active tasks")

# NO calendar events
calendar_events = []

# Prepare data
data_json = {
    "eventos_calendario": calendar_events,
    "tareas_todoist": formatted_tasks
}

# Enhanced prompt - FORCE complete day
prompt = f"""Genera el cronograma del día siguiendo estas instrucciones OBLIGATORIAS:

⚠️ CRÍTICO: El cronograma DEBE cubrir TODO el horario de 07:00 a 21:00 SIN EXCEPCIÓN.
⚠️ CRÍTICO: NO dejes bloques "libres". LLENA cada minuto con tareas reales.
⚠️ CRÍTICO: La última tarea DEBE terminar exactamente a las 21:00.

REGLAS OBLIGATORIAS:

1. NO hay eventos de calendario. Solo organiza las tareas de Todoist.

2. Cada tarea ocupa 20 minutos por defecto.

3. Organiza en bloques de 20 minutos.

4. Alterna tareas intelectuales y administrativas:
   - Etiquetas "motivación", "hábitos" → intelectuales (azul)
   - Etiquetas "obligación", "autopromotor" → administrativas (naranja)
   - Sin etiqueta → inferir por contenido
   - Máximo 2 intelectuales seguidas

5. Llamadas y gestiones → final de la mañana (11:00-14:00)

6. LLENA TODO EL DÍA:
   - 07:00-07:20: Desayunar (fija)
   - 07:20-14:00: Tareas alternadas
   - 14:00-15:00: Comer (fija)
   - 15:00-21:00: MÁS tareas alternadas
   - Total: 14 horas = 42 bloques de 20 min
   - Menos Desayunar (1) y Comer (3) = 38 tareas de Todoist
   
7. Si quedan tareas sin asignar después de llenar hasta las 21:00, ponlas en tabla "Pendientes no asignadas".

8. Prioriza tareas con fecha de vencimiento más cercana.

9. FORMATO DE SALIDA: Solo HTML, nada más.

10. VERIFICACIÓN FINAL: La última fila de la tabla principal DEBE mostrar una hora que termine en 21:00.

DATOS ({len(formatted_tasks)} tareas disponibles):

```json
{json.dumps(data_json, indent=2, ensure_ascii=False)}
```

FORMATO HTML:

<style>
  table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }}
  th, td {{ border: 1px solid #999; padding: 6px 8px; text-align: left; }}
  th {{ background-color: #004080; color: white; }}
  .tarea-fija {{ background-color: #d9ead3; font-weight: bold; }}
  .tarea-intelectual {{ background-color: #cfe2f3; }}
  .tarea-administrativa {{ background-color: #f9cb9c; }}
  .etiqueta {{ display: inline-block; padding: 2px 6px; margin: 0 4px 2px 0; border-radius: 4px; font-size: 12px; color: white; }}
  .motivacion {{ background-color: #6fa8dc; }}
  .habitos {{ background-color: #93c47d; }}
  .obligacion {{ background-color: #e69138; }}
</style>

<h2>📅 Cronograma del Día (07:00 - 21:00)</h2>
<table>
  <thead>
    <tr>
      <th>Hora</th>
      <th>Actividad</th>
      <th>Tipo</th>
      <th>Etiquetas</th>
      <th>Duración</th>
    </tr>
  </thead>
  <tbody>
    <!-- Aquí van TODAS las filas desde 07:00 hasta 21:00 -->
  </tbody>
</table>

<h2>📋 Pendientes no asignadas</h2>
<table>
  <!-- Tareas que no cupieron -->
</table>

RECUERDA: La tabla principal DEBE tener tareas desde 07:00 hasta 21:00 COMPLETO.
"""

print("\n2️⃣ Sending to ChatGPT with STRICT instructions...")
print("   (This may take 40-60 seconds...)")

try:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente experto en organización. DEBES seguir TODAS las instrucciones al pie de la letra. NUNCA dejes un cronograma incompleto. SIEMPRE llena desde 07:00 hasta 21:00."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,  # Even lower for stricter adherence
        max_tokens=5000  # More tokens for complete output
    )
    
    agenda_html = response.choices[0].message.content
    
    print("✅ ChatGPT response received!")
    print(f"   HTML length: {len(agenda_html)} characters")
    
    # Verify it goes to 21:00
    if "21:00" in agenda_html:
        print("✅ VERIFIED: Cronograma reaches 21:00!")
    else:
        print("⚠️  WARNING: Cronograma may not reach 21:00")
    
    # Save to file
    output_file = f"/home/ubuntu/daily-agenda-automation/cronograma_completo_21h_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(agenda_html)
    
    print(f"\n✅ Complete cronograma saved to: {output_file}")
    print("\n" + "="*80)
    print("✅ SUCCESS!")
    print("="*80)
    
    # Count time slots
    import re
    time_slots = re.findall(r'(\d{2}:\d{2}) - (\d{2}:\d{2})', agenda_html)
    if time_slots:
        print(f"\nTime slots found: {len(time_slots)}")
        print(f"First slot: {time_slots[0][0]} - {time_slots[0][1]}")
        print(f"Last slot: {time_slots[-1][0]} - {time_slots[-1][1]}")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
