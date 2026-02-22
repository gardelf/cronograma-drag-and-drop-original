"""
ChatGPT Processor V2
Handles processing of calendar events and tasks using OpenAI API
With custom user-defined prompt
"""

from openai import OpenAI
from typing import List, Dict
import json


class ChatGPTProcessorV2:
    """Process calendar and tasks data using ChatGPT with custom prompt"""
    
    def __init__(self, api_key: str):
        """
        Initialize ChatGPT processor
        
        Args:
            api_key: OpenAI API key
        """
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
        # Prepare the data in JSON format for ChatGPT
        data_json = {
            "eventos_calendario": calendar_events,
            "tareas_todoist": tasks
        }
        
        # Build the custom prompt
        prompt = self._build_custom_prompt(data_json)
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
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
                temperature=0.3,  # Lower temperature for more consistent following of rules
                max_tokens=3000
            )
            
            # Extract the response
            agenda_html = response.choices[0].message.content
            
            return agenda_html
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            # Return a fallback simple table
            return self._create_fallback_table(calendar_events, tasks)
    
    def _build_custom_prompt(self, data_json: Dict) -> str:
        """Build the custom prompt with user-defined rules"""
        
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
{json.dumps(data_json, indent=2, ensure_ascii=False)}
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
        
        return prompt
    
    def _create_fallback_table(self, calendar_events: List[Dict], tasks: List[Dict]) -> str:
        """Create a simple fallback table if API fails"""
        
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th { background-color: #4CAF50; color: white; padding: 12px; text-align: left; }
                td { border: 1px solid #ddd; padding: 10px; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .fixed { background-color: #ffe6e6; }
                .event { background-color: #e6f3ff; }
                .task { background-color: #fff9e6; }
            </style>
        </head>
        <body>
            <h1>📅 Cronograma del Día</h1>
            <table>
                <tr>
                    <th>Hora</th>
                    <th>Actividad</th>
                    <th>Tipo</th>
                    <th>Duración</th>
                </tr>
                <tr class="fixed">
                    <td>07:00 - 07:20</td>
                    <td>Desayunar</td>
                    <td>Tarea fija</td>
                    <td>20 min</td>
                </tr>
        """
        
        # Add events
        for event in calendar_events:
            start = event.get('start_time', 'Sin hora')
            title = event.get('title', 'Sin título')
            html += f"""
                <tr class="event">
                    <td>{start}</td>
                    <td>{title}</td>
                    <td>Evento</td>
                    <td>-</td>
                </tr>
            """
        
        # Add fixed lunch
        html += """
                <tr class="fixed">
                    <td>14:00 - 15:00</td>
                    <td>Comer</td>
                    <td>Tarea fija</td>
                    <td>60 min</td>
                </tr>
        """
        
        # Add tasks
        for task in tasks:
            content = task.get('content', 'Sin título')
            labels = ', '.join(task.get('labels', []))
            html += f"""
                <tr class="task">
                    <td>Por asignar</td>
                    <td>{content}</td>
                    <td>Tarea {labels}</td>
                    <td>20 min</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        
        return html


if __name__ == "__main__":
    # Test the processor
    from config import get_config
    
    config = get_config()
    api_key = config['OPENAI_API_KEY']
    
    if api_key:
        processor = ChatGPTProcessorV2(api_key)
        
        # Test data
        test_events = [
            {"start_time": "09:00", "end_time": "10:00", "title": "Reunión de equipo", "location": "Oficina"},
            {"start_time": "16:00", "end_time": "17:00", "title": "Llamada con cliente"}
        ]
        
        test_tasks = [
            {"content": "Revisar informe", "priority": "Alta", "labels": ["trabajo", "intelectual"], "duration": None},
            {"content": "Llamar al proveedor", "priority": "Media", "labels": ["gestión"], "duration": 15},
            {"content": "Hacer ejercicio", "priority": "Baja", "labels": ["salud", "físico"], "duration": 30}
        ]
        
        result = processor.create_agenda_table(test_events, test_tasks)
        print("Generated agenda:")
        print(result[:500] + "..." if len(result) > 500 else result)
    else:
        print("OPENAI_API_KEY not found in environment")
