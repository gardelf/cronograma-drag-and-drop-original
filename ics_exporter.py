"""
ICS (iCalendar) Exporter
Exports cronograma to ICS format for Google Calendar import
"""

from datetime import datetime, timedelta
from typing import List, Dict
import uuid


class ICSExporter:
    """Export cronograma events to ICS format"""
    
    def __init__(self):
        self.events = []
    
    def add_event(self, title: str, start_time: str, end_time: str, 
                  description: str = "", location: str = "", 
                  priority: str = "P4", task_type: str = "General",
                  url: str = ""):
        """
        Add an event to the calendar
        
        Args:
            title: Event title
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            description: Event description
            location: Event location
            priority: Priority level (P1-P4)
            task_type: Type of task (Física, Intelectual, etc.)
            url: URL to the task
        """
        event = {
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
            "location": location,
            "priority": priority,
            "task_type": task_type,
            "url": url
        }
        self.events.append(event)
    
    def generate_ics(self, date: str = None) -> str:
        """
        Generate ICS file content
        
        Args:
            date: Date in YYYY-MM-DD format. If None, uses today.
            
        Returns:
            ICS file content as string
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Parse the date
        event_date = datetime.strptime(date, "%Y-%m-%d")
        
        # ICS header
        ics_content = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Cronograma Generator//ES",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Cronograma Diario",
            "X-WR-TIMEZONE:Europe/Madrid",
            "X-WR-CALDESC:Cronograma generado automáticamente desde Todoist"
        ]
        
        # Add timezone definition for Europe/Madrid
        ics_content.extend([
            "BEGIN:VTIMEZONE",
            "TZID:Europe/Madrid",
            "BEGIN:STANDARD",
            "DTSTART:19701025T030000",
            "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
            "TZOFFSETFROM:+0200",
            "TZOFFSETTO:+0100",
            "END:STANDARD",
            "BEGIN:DAYLIGHT",
            "DTSTART:19700329T020000",
            "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
            "TZOFFSETFROM:+0100",
            "TZOFFSETTO:+0200",
            "END:DAYLIGHT",
            "END:VTIMEZONE"
        ])
        
        # Add events
        for event in self.events:
            ics_content.extend(self._create_event_ics(event, event_date))
        
        # ICS footer
        ics_content.append("END:VCALENDAR")
        
        return "\r\n".join(ics_content)
    
    def _create_event_ics(self, event: Dict, event_date: datetime) -> List[str]:
        """Create ICS event entry"""
        
        # Parse start and end times
        start_hour, start_min = map(int, event["start_time"].split(":"))
        end_hour, end_min = map(int, event["end_time"].split(":"))
        
        # Create datetime objects
        start_dt = event_date.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
        end_dt = event_date.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)
        
        # Format for ICS (UTC format)
        start_str = start_dt.strftime("%Y%m%dT%H%M%S")
        end_str = end_dt.strftime("%Y%m%dT%H%M%S")
        now_str = datetime.now().strftime("%Y%m%dT%H%M%SZ")
        
        # Generate unique ID
        uid = str(uuid.uuid4())
        
        # Build description
        description_parts = []
        if event.get("task_type"):
            description_parts.append(f"Tipo: {event['task_type']}")
        if event.get("priority"):
            description_parts.append(f"Prioridad: {event['priority']}")
        if event.get("description"):
            description_parts.append(event["description"])
        if event.get("url"):
            description_parts.append(f"\\nEnlace: {event['url']}")
        
        description = "\\n".join(description_parts)
        
        # Map priority to ICS priority (1=highest, 9=lowest)
        priority_map = {"P1": "1", "P2": "3", "P3": "5", "P4": "7", "P-": "9"}
        ics_priority = priority_map.get(event.get("priority", "P4"), "5")
        
        # Create event
        event_ics = [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{now_str}",
            f"DTSTART;TZID=Europe/Madrid:{start_str}",
            f"DTEND;TZID=Europe/Madrid:{end_str}",
            f"SUMMARY:{self._escape_text(event['title'])}",
            f"DESCRIPTION:{self._escape_text(description)}",
            f"PRIORITY:{ics_priority}",
            f"STATUS:CONFIRMED",
            f"TRANSP:OPAQUE"
        ]
        
        # Add categories based on task type
        if event.get("task_type"):
            event_ics.append(f"CATEGORIES:{event['task_type']}")
        
        # Add URL if available
        if event.get("url"):
            event_ics.append(f"URL:{event['url']}")
        
        event_ics.append("END:VEVENT")
        
        return event_ics
    
    def _escape_text(self, text: str) -> str:
        """Escape special characters for ICS format"""
        if not text:
            return ""
        # Escape special characters
        text = text.replace("\\", "\\\\")
        text = text.replace(",", "\\,")
        text = text.replace(";", "\\;")
        text = text.replace("\n", "\\n")
        return text
    
    def save_to_file(self, filename: str, date: str = None):
        """
        Save ICS content to file
        
        Args:
            filename: Output filename
            date: Date in YYYY-MM-DD format
        """
        ics_content = self.generate_ics(date)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(ics_content)


if __name__ == "__main__":
    # Test the exporter
    exporter = ICSExporter()
    
    exporter.add_event(
        title="Reunión de equipo",
        start_time="09:00",
        end_time="10:00",
        description="Revisión semanal del proyecto",
        priority="P1",
        task_type="Administrativa"
    )
    
    exporter.add_event(
        title="Ejercicio matinal",
        start_time="07:00",
        end_time="07:30",
        description="Rutina de ejercicios",
        priority="P2",
        task_type="Física"
    )
    
    # Generate ICS for today
    exporter.save_to_file("/tmp/test_cronograma.ics")
    print("✅ Test ICS file generated: /tmp/test_cronograma.ics")
