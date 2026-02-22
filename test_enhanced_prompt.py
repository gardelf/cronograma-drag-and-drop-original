"""
Test enhanced prompt with:
- Rule 13: Filter only tasks WITH labels
- Rule 14: Exhaustive categorization (Intelectual/Física/Administrativa)
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
print("📅 TESTING ENHANCED PROMPT V3")
print("="*80)

# Get ALL active tasks
print("\n1️⃣ Fetching ALL active tasks from Todoist...")
todoist_client = TodoistClient(config['TODOIST_API_TOKEN'])
all_tasks = todoist_client.get_all_active_tasks()
formatted_tasks = todoist_client.format_tasks_for_display(all_tasks)
print(f"✅ Found {len(formatted_tasks)} active tasks")

# Filter tasks: only those with labels
filtered_tasks = [t for t in formatted_tasks if t.get('labels') and len(t.get('labels', [])) > 0]
tasks_without_labels = [t for t in formatted_tasks if not t.get('labels') or len(t.get('labels', [])) == 0]

print(f"\n📊 Filtering by labels:")
print(f"   ✅ Tasks WITH labels: {len(filtered_tasks)}")
print(f"   ❌ Tasks WITHOUT labels: {len(tasks_without_labels)}")

# Show label distribution
label_counts = {}
for task in filtered_tasks:
    for label in task.get('labels', []):
        label_counts[label] = label_counts.get(label, 0) + 1

print(f"\n🏷️  Label distribution:")
for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"   - {label}: {count} tasks")

# NO calendar events
calendar_events = []

# Prepare data
data_json = {
    "eventos_calendario": calendar_events,
    "tareas_todoist": filtered_tasks
}

# Build enhanced prompt with new rules
prompt = f"""Genera el cronograma del día siguiendo estas instrucciones OBLIGATORIAS:

⚠️ CRÍTICO: El cronograma DEBE cubrir TODO el horario de 07:00 a 21:00 SIN EXCEPCIÓN.
⚠️ CRÍTICO: NO dejes bloques "libres". LLENA cada minuto con tareas reales.
⚠️ CRÍTICO: La última tarea DEBE terminar exactamente a las 21:00.

═══════════════════════════════════════════════════════════════════════════════
REGLAS OBLIGATORIAS:
═══════════════════════════════════════════════════════════════════════════════

1. NO hay eventos de calendario. Solo organiza las tareas de Todoist.

2. Cada tarea ocupa 20 minutos por defecto.

3. Organiza todo en bloques de 20 minutos.

4. Reserva SIEMPRE un bloque fijo de 14:00–15:00 para "Comer".

5. Añade SIEMPRE la tarea "Desayunar" de 20 minutos a las 07:00-07:20.

6. El día empieza a las 07:00 y termina a las 21:00.

7. PRIORIZA tareas con fecha de vencimiento más cercana.

8. Llamadas y gestiones → final de la mañana (11:00-14:00).

9. La última fila DEBE terminar en 21:00.

═══════════════════════════════════════════════════════════════════════════════
13. ⭐ FILTRO DE ETIQUETAS (NUEVA REGLA):
═══════════════════════════════════════════════════════════════════════════════

SOLO incluir tareas que tengan AL MENOS UNA etiqueta.

Etiquetas válidas: motivación, obligación, hábitos, autopromotor, legación

Tareas SIN etiquetas → NO incluir en cronograma.

═══════════════════════════════════════════════════════════════════════════════
14. ⭐ CATEGORIZACIÓN EXHAUSTIVA (NUEVA REGLA):
═══════════════════════════════════════════════════════════════════════════════

Categoriza cada tarea en UNO de estos tres tipos con MÁXIMA PRECISIÓN:

🔵 INTELECTUAL (concentración mental):
   - Leer, estudiar, aprender, diseñar, planificar
   - Reflexionar, meditar, analizar, investigar
   - Ver vídeos educativos, cursos
   - Palabras clave: leer, estudiar, diseñar, planificar, reflexionar, meditar

🟢 FÍSICA (esfuerzo corporal):
   - Ejercicio, deporte, entrenamiento, gimnasio
   - Actividades manuales, movimiento corporal
   - Palabras clave: ejercicio, entrenamiento, deporte, gimnasio, fuerza, yoga, pilates

🟠 ADMINISTRATIVA (gestión, trámites):
   - Llamadas, emails, pagos, trámites
   - Reservas, compras, organización
   - Palabras clave: llamar, pagar, reservar, comprar, contactar, gestión, trámite

CATEGORIZACIÓN:
1. Lee el contenido completo
2. Analiza las etiquetas
3. Identifica palabras clave
4. Asigna la categoría correcta
5. En duda: Física > Intelectual > Administrativa

ALTERNANCIA:
- NO más de 2 tareas del mismo tipo seguidas
- Alterna: Intelectual ↔ Administrativa ↔ Física

═══════════════════════════════════════════════════════════════════════════════
DATOS ({len(filtered_tasks)} tareas CON etiquetas):
═══════════════════════════════════════════════════════════════════════════════

```json
{json.dumps(data_json, indent=2, ensure_ascii=False)}
```

═══════════════════════════════════════════════════════════════════════════════
FORMATO HTML:
═══════════════════════════════════════════════════════════════════════════════

<style>
  table {{ border-collapse: collapse; width: 100%; font-family: Arial, sans-serif; }}
  th, td {{ border: 1px solid #999; padding: 6px 8px; text-align: left; }}
  th {{ background-color: #004080; color: white; }}
  .tarea-fija {{ background-color: #d9ead3; font-weight: bold; }}
  .tarea-intelectual {{ background-color: #cfe2f3; }}
  .tarea-fisica {{ background-color: #c9f0dd; }}
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
    <!-- SOLO tareas CON etiquetas, categorizadas correctamente -->
  </tbody>
</table>

<h2>📋 Tareas Excluidas</h2>
<p>Tareas sin etiquetas ({len(tasks_without_labels)}) o que no cupieron:</p>
<table>
  <thead>
    <tr>
      <th>Actividad</th>
      <th>Motivo</th>
    </tr>
  </thead>
  <tbody>
    <!-- Tareas sin etiquetas -->
  </tbody>
</table>
"""

print("\n2️⃣ Sending enhanced prompt to ChatGPT...")
print("   (This may take 40-60 seconds...)")

try:
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """Eres un asistente experto en organización. 
Sigues TODAS las instrucciones al pie de la letra.
Eres EXHAUSTIVO en la categorización de tareas.
NUNCA dejas un cronograma incompleto."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=5000
    )
    
    agenda_html = response.choices[0].message.content
    
    print("✅ ChatGPT response received!")
    print(f"   HTML length: {len(agenda_html)} characters")
    
    # Verify
    if "21:00" in agenda_html:
        print("✅ VERIFIED: Reaches 21:00")
    
    # Count categorizations
    intelectual_count = agenda_html.count('tarea-intelectual')
    fisica_count = agenda_html.count('tarea-fisica')
    administrativa_count = agenda_html.count('tarea-administrativa')
    
    print(f"\n📊 Categorization breakdown:")
    print(f"   🔵 Intelectual: {intelectual_count} tasks")
    print(f"   🟢 Física: {fisica_count} tasks")
    print(f"   🟠 Administrativa: {administrativa_count} tasks")
    
    # Save
    output_file = f"/home/ubuntu/daily-agenda-automation/cronograma_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(agenda_html)
    
    print(f"\n✅ Enhanced cronograma saved to:")
    print(f"   {output_file}")
    print("\n" + "="*80)
    print("✅ SUCCESS! ENHANCED PROMPT WITH NEW RULES!")
    print("="*80)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
