"""
Test script to analyze all available fields in calendar events
"""

import os
from datetime import datetime, timedelta
from caldav import DAVClient
from icalendar import Calendar
import pytz
from dotenv import load_dotenv

load_dotenv()

username = os.getenv('ICLOUD_USERNAME')
password = os.getenv('ICLOUD_APP_PASSWORD')
caldav_url = "https://caldav.icloud.com/"
timezone = pytz.timezone('Europe/Madrid')

client = DAVClient(url=caldav_url, username=username, password=password)
principal = client.principal()
calendars = principal.calendars()

today = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
tomorrow = today + timedelta(days=1)

print("=" * 80)
print("🔍 ANÁLISIS DETALLADO DE CAMPOS DE EVENTOS")
print("=" * 80)

for calendar in calendars:
    calendar_name = calendar.name
    print(f"\n📅 Calendario: {calendar_name}")
    
    try:
        events = calendar.date_search(start=today, end=tomorrow, expand=True)
        
        for event in events:
            try:
                cal = Calendar.from_ical(event.data)
                
                for component in cal.walk():
                    if component.name == "VEVENT":
                        summary = str(component.get('summary', 'Sin título'))
                        print(f"\n{'=' * 80}")
                        print(f"📌 EVENTO: {summary}")
                        print(f"{'=' * 80}")
                        
                        # List all available fields
                        print("\n🔑 TODOS LOS CAMPOS DISPONIBLES:")
                        for key in sorted(component.keys()):
                            value = component.get(key)
                            print(f"  • {key}: {value}")
                        
                        # Specific fields of interest
                        print("\n👤 INFORMACIÓN DE AUTOR/ORGANIZADOR:")
                        
                        organizer = component.get('organizer')
                        if organizer:
                            print(f"  • ORGANIZER: {organizer}")
                            if hasattr(organizer, 'params'):
                                print(f"    Parámetros: {organizer.params}")
                        else:
                            print("  • ORGANIZER: No disponible")
                        
                        attendees = component.get('attendee')
                        if attendees:
                            print(f"  • ATTENDEE: {attendees}")
                        else:
                            print("  • ATTENDEE: No disponible")
                        
                        created = component.get('created')
                        if created:
                            print(f"  • CREATED: {created}")
                        
                        last_modified = component.get('last-modified')
                        if last_modified:
                            print(f"  • LAST-MODIFIED: {last_modified}")
                        
                        uid = component.get('uid')
                        if uid:
                            print(f"  • UID: {uid}")
                        
                        status = component.get('status')
                        if status:
                            print(f"  • STATUS: {status}")
                        
                        description = component.get('description')
                        if description:
                            print(f"  • DESCRIPTION: {description}")
                        
                        location = component.get('location')
                        if location:
                            print(f"  • LOCATION: {location}")
            
            except Exception as e:
                print(f"  ⚠️  Error procesando evento: {e}")
                continue
    
    except Exception as e:
        print(f"  ⚠️  Error accediendo al calendario: {e}")
        continue

print("\n" + "=" * 80)
print("✅ Análisis completado")
print("=" * 80)
