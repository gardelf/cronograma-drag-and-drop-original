"""
iCloud Calendar Client using CalDAV
Reads events from iCloud Calendar to use as fixed blocks in the daily schedule
"""

import os
from datetime import datetime, timedelta
from caldav import DAVClient
from icalendar import Calendar
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class iCloudCalendarClient:
    """Client to interact with iCloud Calendar via CalDAV protocol"""
    
    def __init__(self):
        """Initialize CalDAV client with iCloud credentials from environment variables"""
        self.username = os.getenv('ICLOUD_USERNAME')  # tu_email@icloud.com
        self.password = os.getenv('ICLOUD_APP_PASSWORD')  # Contraseña específica de app
        self.caldav_url = "https://caldav.icloud.com/"
        self.timezone = pytz.timezone('Europe/Madrid')
        
        if not self.username or not self.password:
            print("⚠️  ADVERTENCIA: Credenciales de iCloud no configuradas")
            print(f"   ICLOUD_USERNAME: {self.username}")
            print(f"   ICLOUD_APP_PASSWORD exists: {bool(self.password)}")
            print("   Configura ICLOUD_USERNAME y ICLOUD_APP_PASSWORD en variables de entorno")
            self.client = None
        else:
            try:
                self.client = DAVClient(
                    url=self.caldav_url,
                    username=self.username,
                    password=self.password
                )
                print("✅ Conectado a iCloud Calendar")
            except Exception as e:
                print(f"❌ Error al conectar con iCloud Calendar: {e}")
                self.client = None
    
    def get_week_events(self, days=7):
        """
        Get all events from iCloud Calendar for the next N days
        
        Args:
            days: Number of days to fetch (default 7)
        
        Returns:
            dict: Dictionary with dates as keys and list of events as values
                {
                    '2024-12-04': [
                        {
                            'summary': 'Event title',
                            'start': datetime object,
                            'end': datetime object,
                            'all_day': bool
                        }
                    ]
                }
        """
        if not self.client:
            print("⚠️  Cliente CalDAV no disponible, devolviendo diccionario vacío")
            return {}
        
        try:
            # Get principal and calendars
            principal = self.client.principal()
            calendars = principal.calendars()
            
            # Define date range
            today = datetime.now(self.timezone).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today + timedelta(days=days)
            
            print(f"\n📅 Buscando eventos del calendario para {days} días: {today.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
            
            events_by_date = {}
            
            # Iterate through all calendars - ONLY read from personal calendar "Calendario"
            for calendar in calendars:
                calendar_name = calendar.name
                
                # SKIP shared calendar "Casa Juana Doña"
                if calendar_name == "Casa Juana Doña":
                    print(f"   ⏭️  Saltando calendario compartido: {calendar_name}")
                    continue
                
                print(f"   Revisando calendario: {calendar_name}")
                
                try:
                    # Search events in date range
                    events = calendar.date_search(start=today, end=end_date, expand=True)
                    
                    for event in events:
                        try:
                            # Parse iCalendar data
                            cal = Calendar.from_ical(event.data)
                            
                            for component in cal.walk():
                                if component.name == "VEVENT":
                                    # Extract event details
                                    summary = str(component.get('summary', 'Sin título'))
                                    dtstart = component.get('dtstart')
                                    dtend = component.get('dtend')
                                    
                                    if not dtstart:
                                        continue
                                    
                                    # Get datetime objects
                                    start_dt_raw = dtstart.dt
                                    end_dt_raw = dtend.dt if dtend else None
                                    
                                    # Handle both datetime and date objects
                                    if isinstance(start_dt_raw, datetime):
                                        # It's a datetime (timed event)
                                        start_dt = start_dt_raw
                                        if start_dt.tzinfo is None:
                                            start_dt = self.timezone.localize(start_dt)
                                        else:
                                            start_dt = start_dt.astimezone(self.timezone)
                                        
                                        if end_dt_raw and isinstance(end_dt_raw, datetime):
                                            end_dt = end_dt_raw
                                            if end_dt.tzinfo is None:
                                                end_dt = self.timezone.localize(end_dt)
                                            else:
                                                end_dt = end_dt.astimezone(self.timezone)
                                        else:
                                            end_dt = start_dt + timedelta(hours=1)
                                        
                                        all_day = False
                                    else:
                                        # It's a date (all-day event)
                                        start_dt = self.timezone.localize(datetime.combine(start_dt_raw, datetime.min.time()))
                                        if end_dt_raw:
                                            end_dt = self.timezone.localize(datetime.combine(end_dt_raw, datetime.min.time()))
                                        else:
                                            end_dt = start_dt + timedelta(days=1)
                                        all_day = True
                                    
                                    # Get date key
                                    date_key = start_dt.strftime('%Y-%m-%d')
                                    
                                    # Add event to dictionary
                                    if date_key not in events_by_date:
                                        events_by_date[date_key] = []
                                    
                                    events_by_date[date_key].append({
                                        'summary': summary,
                                        'start': start_dt,
                                        'end': end_dt,
                                        'all_day': all_day
                                    })
                                    print(f"      ✓ {date_key} - {start_dt.strftime('%H:%M') if not all_day else 'TODO DÍA'}: {summary}")
                        
                        except Exception as e:
                            print(f"      ⚠️  Error al procesar evento: {e}")
                            continue
                
                except Exception as e:
                    print(f"   ⚠️  Error al buscar eventos en {calendar_name}: {e}")
                    continue
            
            # Sort events by start time for each day
            for date_key in events_by_date:
                events_by_date[date_key].sort(key=lambda x: x['start'])
            
            print(f"\n✅ Encontrados eventos en {len(events_by_date)} días")
            return events_by_date
        
        except Exception as e:
            print(f"❌ Error al obtener eventos de la semana: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def get_today_events(self, target_date=None):
        """
        Get all events from iCloud Calendar for a specific date
        
        Args:
            target_date: datetime object for the target date (default: today)
        
        Returns:
            list: List of events in the format:
                {
                    'content': 'Event title',
                    'start_time': '09:00',
                    'end_time': '10:30',
                    'duration': 90,
                    'type': 'Fija',
                    'priority': 'P1',
                    'labels': ['calendario'],
                    'source': 'calendar'
                }
        """
        if not self.client:
            print("⚠️  Cliente CalDAV no disponible, devolviendo lista vacía")
            return []
        
        try:
            # Get principal and calendars
            principal = self.client.principal()
            calendars = principal.calendars()
            
            # Define target date's time range
            if target_date is None:
                target_date = datetime.now(self.timezone)
            today = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            print(f"\n📅 Buscando eventos del calendario para: {today.strftime('%d/%m/%Y')}")
            
            events_list = []
            
            # Iterate through all calendars - ONLY read from personal calendar "Calendario"
            for calendar in calendars:
                calendar_name = calendar.name
                
                # SKIP shared calendar "Casa Juana Doña" - those events are handled separately
                if calendar_name == "Casa Juana Doña":
                    print(f"   ⏭️  Saltando calendario compartido: {calendar_name}")
                    continue
                
                print(f"   Revisando calendario: {calendar_name}")
                
                try:
                    # Search events in date range
                    events = calendar.date_search(start=today, end=tomorrow, expand=True)
                    
                    for event in events:
                        try:
                            # Parse iCalendar data
                            cal = Calendar.from_ical(event.data)
                            
                            for component in cal.walk():
                                if component.name == "VEVENT":
                                    # Extract event details
                                    summary = str(component.get('summary', 'Sin título'))
                                    dtstart = component.get('dtstart').dt
                                    dtend = component.get('dtend').dt
                                    
                                    # Convert to datetime if date only
                                    if isinstance(dtstart, datetime):
                                        start_dt = dtstart.astimezone(self.timezone)
                                        end_dt = dtend.astimezone(self.timezone)
                                    else:
                                        # All-day event, skip for now
                                        continue
                                    
                                    # Format times
                                    start_time = start_dt.strftime('%H:%M')
                                    end_time = end_dt.strftime('%H:%M')
                                    
                                    # Calculate duration in minutes
                                    duration = int((end_dt - start_dt).total_seconds() / 60)
                                    
                                    # Create event dict
                                    event_dict = {
                                        'content': f"📅 {summary}",
                                        'start_time': start_time,
                                        'end_time': end_time,
                                        'duration': duration,
                                        'type': 'Fija',
                                        'priority': 'P1',  # Maximum priority
                                        'priority_value': 4,  # Todoist format
                                        'labels': ['calendario', calendar_name],
                                        'source': 'calendar',
                                        'url': None
                                    }
                                    
                                    events_list.append(event_dict)
                                    print(f"      ✓ {start_time}-{end_time}: {summary}")
                        
                        except Exception as e:
                            print(f"      ⚠️  Error procesando evento: {e}")
                            continue
                
                except Exception as e:
                    print(f"   ⚠️  Error accediendo al calendario {calendar_name}: {e}")
                    continue
            
            print(f"\n✅ Total de eventos encontrados: {len(events_list)}")
            return events_list
        
        except Exception as e:
            print(f"❌ Error al obtener eventos del calendario: {e}")
            return []
    
    def get_events_from_calendar_range(self, calendar_name, start_date, end_date):
        """
        Get events from a specific calendar within a date range
        
        Args:
            calendar_name: Name of the calendar
            start_date: Start datetime
            end_date: End datetime
        
        Returns:
            List of events
        """
        if not self.client:
            return []
        
        events = []
        
        try:
            principal = self.client.principal()
            calendars = principal.calendars()
            
            for calendar in calendars:
                if calendar.name == calendar_name:
                    try:
                        cal_events = calendar.date_search(start=start_date, end=end_date, expand=True)
                        
                        for event in cal_events:
                            try:
                                cal = Calendar.from_ical(event.data)
                                
                                for component in cal.walk():
                                    if component.name == "VEVENT":
                                        summary = str(component.get('summary', 'Sin título'))
                                        dtstart = component.get('dtstart').dt
                                        dtend = component.get('dtend').dt
                                        uid = str(component.get('uid', ''))
                                        
                                        # Convert to timezone-aware datetime
                                        if isinstance(dtstart, datetime):
                                            if dtstart.tzinfo is None:
                                                dtstart = self.timezone.localize(dtstart)
                                            else:
                                                dtstart = dtstart.astimezone(self.timezone)
                                        else:
                                            # All-day event, skip
                                            continue
                                        
                                        if isinstance(dtend, datetime):
                                            if dtend.tzinfo is None:
                                                dtend = self.timezone.localize(dtend)
                                            else:
                                                dtend = dtend.astimezone(self.timezone)
                                        
                                        events.append({
                                            'uid': uid,
                                            'summary': summary,
                                            'start_time': dtstart.strftime('%H:%M'),
                                            'end_time': dtend.strftime('%H:%M'),
                                            'date': dtstart.strftime('%d/%m/%Y'),
                                            'start_datetime': dtstart,
                                            'end_datetime': dtend
                                        })
                            except Exception as e:
                                print(f"Error processing event: {e}")
                                continue
                    
                    except Exception as e:
                        print(f"Error searching calendar: {e}")
                    
                    break
        
        except Exception as e:
            print(f"Error accessing calendars: {e}")
        
        return events
    
    def create_event(self, calendar_name, summary, start_datetime, end_datetime, description=""):
        """
        Create a new event in the specified calendar
        
        Args:
            calendar_name: Name of the calendar to add the event to
            summary: Event title/summary
            start_datetime: Start datetime (datetime object with timezone)
            end_datetime: End datetime (datetime object with timezone)
            description: Event description (optional)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.client:
                print("❌ Calendar client not initialized")
                return False
            
            principal = self.client.principal()
            calendars = principal.calendars()
            
            # Find the target calendar
            target_calendar = None
            for calendar in calendars:
                if calendar.name == calendar_name:
                    target_calendar = calendar
                    break
            
            if not target_calendar:
                print(f"❌ Calendar '{calendar_name}' not found")
                return False
            
            # Create iCalendar event
            from icalendar import Event as iCalEvent
            import uuid
            
            event = iCalEvent()
            event.add('summary', summary)
            event.add('dtstart', start_datetime)
            event.add('dtend', end_datetime)
            event.add('dtstamp', datetime.now(self.timezone))
            event.add('uid', str(uuid.uuid4()))
            
            if description:
                event.add('description', description)
            
            # Create calendar wrapper
            cal = Calendar()
            cal.add('prodid', '-//Daily Agenda Automation//manus.im//')
            cal.add('version', '2.0')
            cal.add_component(event)
            
            # Save event to calendar
            target_calendar.save_event(cal.to_ical().decode('utf-8'))
            
            print(f"✅ Event '{summary}' created successfully in '{calendar_name}'")
            return True
        
        except Exception as e:
            print(f"❌ Error creating event: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_events_summary(self):
        """Get a summary of today's calendar events"""
        events = self.get_today_events()
        
        if not events:
            return "No hay eventos en el calendario para hoy"
        
        summary = f"Eventos del calendario ({len(events)}):\n"
        for event in sorted(events, key=lambda x: x['start_time']):
            summary += f"  • {event['start_time']}-{event['end_time']}: {event['content']}\n"
        
        return summary


# Test function
if __name__ == "__main__":
    print("=" * 80)
    print("🧪 TEST: iCloud Calendar Client")
    print("=" * 80)
    
    # Create client
    client = iCloudCalendarClient()
    
    # Get today's events
    events = client.get_today_events()
    
    # Print summary
    print("\n" + "=" * 80)
    print(client.get_events_summary())
    print("=" * 80)
    
    # Print detailed event info
    if events:
        print("\n📋 Formato detallado de eventos:")
        for i, event in enumerate(events, 1):
            print(f"\n{i}. {event['content']}")
            print(f"   Horario: {event['start_time']} - {event['end_time']}")
            print(f"   Duración: {event['duration']} minutos")
            print(f"   Tipo: {event['type']}")
            print(f"   Prioridad: {event['priority']}")
            print(f"   Etiquetas: {', '.join(event['labels'])}")
