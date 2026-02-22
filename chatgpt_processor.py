"""
ChatGPT Processor
Handles processing of calendar events and tasks using OpenAI API
"""

from openai import OpenAI
from typing import List, Dict
import json


class ChatGPTProcessor:
    """Process calendar and tasks data using ChatGPT"""
    
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
        # Prepare the prompt
        prompt = self._build_prompt(calendar_events, tasks)
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un asistente de productividad experto. Tu tarea es organizar eventos de calendario y tareas pendientes en una agenda diaria optimizada.

Debes:
1. Ordenar cronológicamente por horario
2. Las tareas sin hora específica deben distribuirse inteligentemente en huecos libres
3. Priorizar según urgencia e importancia
4. Generar una tabla HTML bien formateada y profesional
5. Usar colores para diferenciar prioridades
6. Incluir estimaciones de duración cuando sea posible"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extract the response
            agenda_html = response.choices[0].message.content
            
            return agenda_html
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            # Return a fallback simple table
            return self._create_fallback_table(calendar_events, tasks)
    
    def _build_prompt(self, calendar_events: List[Dict], tasks: List[Dict]) -> str:
        """Build the prompt for ChatGPT"""
        
        prompt = """Tengo los siguientes eventos de calendario y tareas pendientes para hoy. 
Organízalos en una tabla HTML profesional y bien estructurada.

FORMATO DE LA TABLA:
- Usa HTML con estilos CSS inline
- Columnas: Hora | Actividad | Tipo | Prioridad | Duración
- Ordena cronológicamente
- Usa colores: 
  * Rojo para prioridad Urgente
  * Naranja para prioridad Alta
  * Amarillo para prioridad Media
  * Verde para prioridad Baja
- Incluye un título "📅 Agenda del Día"
- Haz la tabla responsive y profesional

"""
        
        # Add calendar events
        if calendar_events:
            prompt += "\n📅 EVENTOS DEL CALENDARIO:\n"
            for event in calendar_events:
                prompt += f"- {event.get('start_time', 'Sin hora')}: {event.get('title', 'Sin título')}"
                if event.get('location'):
                    prompt += f" (Ubicación: {event['location']})"
                prompt += "\n"
        else:
            prompt += "\n📅 EVENTOS DEL CALENDARIO: Ninguno\n"
        
        # Add tasks
        if tasks:
            prompt += "\n✅ TAREAS PENDIENTES DE TODOIST:\n"
            for task in tasks:
                prompt += f"- {task.get('content', 'Sin título')}"
                if task.get('due_time'):
                    prompt += f" (Hora: {task['due_time']})"
                prompt += f" [Prioridad: {task.get('priority', 'Baja')}]"
                if task.get('labels'):
                    prompt += f" {task['labels']}"
                prompt += "\n"
        else:
            prompt += "\n✅ TAREAS PENDIENTES: Ninguna\n"
        
        prompt += """
\nDevuelve SOLO el código HTML de la tabla, sin explicaciones adicionales.
La tabla debe ser completa, profesional y lista para enviar por email."""
        
        return prompt
    
    def _create_fallback_table(self, calendar_events: List[Dict], tasks: List[Dict]) -> str:
        """Create a simple fallback table if API fails"""
        
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                h1 { color: #333; }
                table { border-collapse: collapse; width: 100%; margin-top: 20px; }
                th { background-color: #4CAF50; color: white; padding: 12px; text-align: left; }
                td { border: 1px solid #ddd; padding: 10px; }
                tr:nth-child(even) { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>📅 Agenda del Día</h1>
            <table>
                <tr>
                    <th>Hora</th>
                    <th>Actividad</th>
                    <th>Tipo</th>
                    <th>Prioridad</th>
                </tr>
        """
        
        # Add events
        for event in calendar_events:
            html += f"""
                <tr>
                    <td>{event.get('start_time', 'Sin hora')}</td>
                    <td>{event.get('title', 'Sin título')}</td>
                    <td>Evento</td>
                    <td>-</td>
                </tr>
            """
        
        # Add tasks
        for task in tasks:
            html += f"""
                <tr>
                    <td>{task.get('due_time', 'Por definir')}</td>
                    <td>{task.get('content', 'Sin título')}</td>
                    <td>Tarea</td>
                    <td>{task.get('priority', 'Baja')}</td>
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
        processor = ChatGPTProcessor(api_key)
        
        # Test data
        test_events = [
            {"start_time": "09:00", "title": "Reunión de equipo", "location": "Oficina"},
            {"start_time": "14:00", "title": "Comida con cliente"}
        ]
        
        test_tasks = [
            {"content": "Revisar informe", "priority": "Alta", "due_time": "11:00"},
            {"content": "Llamar al proveedor", "priority": "Media", "due_time": None}
        ]
        
        result = processor.create_agenda_table(test_events, test_tasks)
        print("Generated agenda:")
        print(result[:500] + "..." if len(result) > 500 else result)
    else:
        print("OPENAI_API_KEY not found in environment")
