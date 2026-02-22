"""
ChatGPT Processor V3
Enhanced version with strict filtering and categorization rules
"""

from openai import OpenAI
from typing import List, Dict
import json


class ChatGPTProcessorV3:
    """Process calendar and tasks data using ChatGPT with enhanced rules"""
    
    def __init__(self, api_key: str):
        """Initialize ChatGPT processor"""
        self.client = OpenAI(api_key=api_key)
    
    def create_agenda_table(self, calendar_events: List[Dict], tasks: List[Dict]) -> str:
        """
        Process calendar events and tasks to create organized agenda table
        
        Args:
            calendar_events: List of calendar event dictionaries
            tasks: List of task dictionaries from Todoist
            
        Returns:
            HTML formatted table with organized agenda
        """
        # Filter tasks: only those with labels
        filtered_tasks = [t for t in tasks if t.get('labels') and len(t.get('labels', [])) > 0]
        tasks_without_labels = [t for t in tasks if not t.get('labels') or len(t.get('labels', [])) == 0]
        
        print(f"📊 Filtered tasks: {len(filtered_tasks)} with labels, {len(tasks_without_labels)} without labels")
        
        # Prepare data
        data_json = {
            "eventos_calendario": calendar_events,
            "tareas_todoist": filtered_tasks
        }
        
        # Build enhanced prompt
        prompt = self._build_enhanced_prompt(data_json, tasks_without_labels)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un asistente experto en organización de tiempo y productividad. 
Sigues las instrucciones al pie de la letra con MÁXIMA PRECISIÓN.
Eres EXHAUSTIVO en la categorización de tareas según su naturaleza (intelectual/física/administrativa).
NUNCA dejas un cronograma incompleto. SIEMPRE llenas desde 07:00 hasta 21:00."""
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
            return agenda_html
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return self._create_fallback_table(calendar_events, filtered_tasks)
    
    def _build_enhanced_prompt(self, data_json: Dict, tasks_without_labels: List[Dict]) -> str:
        """Build the enhanced prompt with strict rules"""
        
        prompt = f"""Genera el cronograma del día siguiendo estas instrucciones OBLIGATORIAS:

⚠️ CRÍTICO: El cronograma DEBE cubrir TODO el horario de 07:00 a 21:00 SIN EXCEPCIÓN.
⚠️ CRÍTICO: NO dejes bloques "libres". LLENA cada minuto con tareas reales.
⚠️ CRÍTICO: La última tarea DEBE terminar exactamente a las 21:00.

═══════════════════════════════════════════════════════════════════════════════
REGLAS OBLIGATORIAS:
═══════════════════════════════════════════════════════════════════════════════

1. Respeta EXACTAMENTE los eventos del calendario: no modificarlos, no moverlos.

2. Coloca las tareas de Todoist en los huecos disponibles entre eventos.

3. Cada tarea ocupa 20 minutos por defecto.

4. Organiza todo en bloques de 20 minutos (subdivisiones de 10 o 5 solo si es necesario).

5. Reserva SIEMPRE un bloque fijo de 14:00–15:00 para "Comer".
   - Es un evento fijo del día.
   - No puede ser movido ni sustituido.

6. Añade SIEMPRE la tarea "Desayunar" de 20 minutos al inicio.
   - Debe colocarse a las 07:00-07:20.
   - Tipo = "Tarea fija".

7. El día empieza a las 07:00 y termina a las 21:00.
   - Solo puedes utilizar ese intervalo para organizar tareas y eventos.
   - Nada puede colocarse antes de las 07:00 ni después de las 21:00.

8. PRIORIZA tareas con fecha de vencimiento (due_date) más cercana.

9. Las llamadas y gestiones cortas → al final de la mañana (11:00-14:00) siempre que sea posible.

10. Si quedan tareas sin asignar después de llenar hasta las 21:00, ponlas en tabla "Pendientes no asignadas".

11. No devuelvas nada más que las tablas HTML.

12. VERIFICACIÓN FINAL: La última fila de la tabla principal DEBE mostrar una hora que termine en 21:00.

═══════════════════════════════════════════════════════════════════════════════
13. ⭐ FILTRO DE ETIQUETAS (NUEVA REGLA):
═══════════════════════════════════════════════════════════════════════════════

SOLO incluir en el cronograma tareas que tengan AL MENOS UNA etiqueta.

Etiquetas válidas:
- motivación
- obligación
- hábitos
- autopromotor
- legación

Tareas SIN etiquetas → NO incluir en cronograma principal, ir directamente a "Pendientes no asignadas".

═══════════════════════════════════════════════════════════════════════════════
14. ⭐ CATEGORIZACIÓN EXHAUSTIVA (NUEVA REGLA):
═══════════════════════════════════════════════════════════════════════════════

Debes categorizar cada tarea en UNO de estos tres tipos con MÁXIMA PRECISIÓN:

🔵 INTELECTUAL (requiere concentración mental, esfuerzo cognitivo):
   Ejemplos:
   - Leer libros, estudiar, aprender
   - Planificar proyectos, diseñar, crear
   - Reflexionar, meditar, pensar estratégicamente
   - Ver vídeos educativos, cursos
   - Escribir, redactar, analizar
   - Investigar, buscar información
   - Tareas con etiquetas: "motivación" (generalmente), "hábitos" (si son mentales)
   
   Palabras clave: leer, estudiar, aprender, diseñar, planificar, reflexionar, 
                    meditar, analizar, investigar, pensar, crear, escribir

🟢 FÍSICA (requiere esfuerzo corporal, movimiento):
   Ejemplos:
   - Ejercicio, deporte, entrenamiento
   - Gimnasio, correr, nadar, yoga
   - Actividades manuales, construcción
   - Tareas domésticas físicas
   - Cualquier actividad que implique movimiento corporal significativo
   - Tareas con etiquetas: "hábitos" (si son físicos)
   
   Palabras clave: ejercicio, entrenamiento, deporte, gimnasio, físico, 
                    correr, nadar, yoga, pilates, fuerza, cardio

🟠 ADMINISTRATIVA (gestión, trámites, organización):
   Ejemplos:
   - Llamadas telefónicas, emails
   - Pagos, trámites, gestiones bancarias
   - Reservas, compras online
   - Organización de documentos
   - Contactar personas, seguimiento
   - Tareas con etiquetas: "obligación", "autopromotor", "legación"
   
   Palabras clave: llamar, pagar, reservar, comprar, contactar, gestión,
                    trámite, email, organizar, formulario, impuesto

INSTRUCCIONES DE CATEGORIZACIÓN:

1. Lee el CONTENIDO completo de la tarea
2. Analiza las ETIQUETAS de la tarea
3. Identifica PALABRAS CLAVE en el contenido
4. Asigna la categoría que mejor represente la NATURALEZA PRINCIPAL de la tarea
5. En caso de duda, prioriza: Física > Intelectual > Administrativa

ALTERNANCIA OBLIGATORIA:

- Alterna entre tipos de tareas para evitar fatiga
- NO más de 2 tareas del mismo tipo seguidas
- Prioridad de alternancia: Intelectual ↔ Administrativa ↔ Física
- Ejemplo correcto: Intelectual → Administrativa → Intelectual → Física → Administrativa
- Ejemplo INCORRECTO: Intelectual → Intelectual → Intelectual (máximo 2 seguidas)

═══════════════════════════════════════════════════════════════════════════════
DATOS DEL DÍA:
═══════════════════════════════════════════════════════════════════════════════

Total de tareas CON etiquetas disponibles: {len(data_json['tareas_todoist'])}
Total de tareas SIN etiquetas (excluidas): {len(tasks_without_labels)}

```json
{json.dumps(data_json, indent=2, ensure_ascii=False)}
```

═══════════════════════════════════════════════════════════════════════════════
FORMATO DE SALIDA HTML:
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
  .autopromotor {{ background-color: #f6b26b; }}
  .legacion {{ background-color: #999999; }}
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
    <!-- Tareas desde 07:00 hasta 21:00 -->
  </tbody>
</table>

<h2>📋 Pendientes no asignadas</h2>
<p>Tareas sin etiquetas o que no cupieron en el cronograma:</p>
<table>
  <thead>
    <tr>
      <th>Actividad</th>
      <th>Etiquetas</th>
      <th>Motivo</th>
    </tr>
  </thead>
  <tbody>
    <!-- Tareas excluidas -->
  </tbody>
</table>

RECUERDA: 
- Solo tareas CON etiquetas en el cronograma principal
- Categorización EXHAUSTIVA (Intelectual/Física/Administrativa)
- Cronograma COMPLETO hasta 21:00
"""
        
        return prompt
    
    def _create_fallback_table(self, calendar_events: List[Dict], tasks: List[Dict]) -> str:
        """Create a simple fallback table if API fails"""
        # Similar to previous version
        return "<html><body><h1>Error generating agenda</h1></body></html>"


if __name__ == "__main__":
    print("ChatGPT Processor V3 - Enhanced with filtering and categorization")
