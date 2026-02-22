"""
Deep analysis of all event fields including Apple custom fields
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

print("=" * 100)
print("🔬 ANÁLISIS PROFUNDO DE EVENTOS - CALENDARIO COMPARTIDO")
print("=" * 100)

for calendar in calendars:
    calendar_name = calendar.name
    
    # Focus on shared calendar
    if "Casa Juana Doña" not in calendar_name:
        continue
    
    print(f"\n📅 Analizando calendario: {calendar_name}")
    print(f"{'=' * 100}")
    
    try:
        events = calendar.date_search(start=today, end=tomorrow, expand=True)
        
        for event in events:
            try:
                # Get raw iCalendar data
                raw_data = event.data
                
                cal = Calendar.from_ical(raw_data)
                
                for component in cal.walk():
                    if component.name == "VEVENT":
                        summary = str(component.get('summary', 'Sin título'))
                        
                        print(f"\n{'=' * 100}")
                        print(f"📌 EVENTO: {summary}")
                        print(f"{'=' * 100}")
                        
                        # Print ALL fields (including X- custom fields)
                        print("\n🔑 TODOS LOS CAMPOS (incluidos campos personalizados X-):")
                        for key in sorted(component.keys()):
                            value = component.get(key)
                            
                            # Special handling for complex fields
                            if hasattr(value, 'params'):
                                print(f"\n  • {key}: {value}")
                                print(f"    Parámetros: {value.params}")
                            else:
                                print(f"  • {key}: {value}")
                        
                        # Look for Apple-specific fields
                        print("\n🍎 CAMPOS ESPECÍFICOS DE APPLE:")
                        apple_fields = [k for k in component.keys() if k.startswith('X-APPLE')]
                        if apple_fields:
                            for field in apple_fields:
                                value = component.get(field)
                                print(f"  • {field}: {value}")
                        else:
                            print("  • No se encontraron campos X-APPLE-*")
                        
                        # Look for any X- custom fields
                        print("\n🔧 OTROS CAMPOS PERSONALIZADOS (X-):")
                        x_fields = [k for k in component.keys() if k.startswith('X-') and not k.startswith('X-APPLE')]
                        if x_fields:
                            for field in x_fields:
                                value = component.get(field)
                                print(f"  • {field}: {value}")
                        else:
                            print("  • No se encontraron otros campos X-*")
                        
                        # Check for ORGANIZER and ATTENDEE
                        print("\n👥 INFORMACIÓN DE PARTICIPANTES:")
                        
                        organizer = component.get('ORGANIZER')
                        if organizer:
                            print(f"  • ORGANIZER encontrado:")
                            print(f"    Valor: {organizer}")
                            if hasattr(organizer, 'params'):
                                print(f"    Parámetros: {dict(organizer.params)}")
                        else:
                            print("  • ORGANIZER: No disponible")
                        
                        attendee = component.get('ATTENDEE')
                        if attendee:
                            print(f"  • ATTENDEE encontrado:")
                            if isinstance(attendee, list):
                                for i, att in enumerate(attendee, 1):
                                    print(f"    {i}. {att}")
                                    if hasattr(att, 'params'):
                                        print(f"       Parámetros: {dict(att.params)}")
                            else:
                                print(f"    Valor: {attendee}")
                                if hasattr(attendee, 'params'):
                                    print(f"    Parámetros: {dict(attendee.params)}")
                        else:
                            print("  • ATTENDEE: No disponible")
                        
                        # Print raw data snippet
                        print("\n📄 FRAGMENTO DE DATOS RAW (primeras 50 líneas):")
                        raw_lines = raw_data.decode('utf-8').split('\n')
                        for i, line in enumerate(raw_lines[:50], 1):
                            if 'X-' in line or 'ORGANIZER' in line or 'ATTENDEE' in line or 'CREATOR' in line:
                                print(f"  {i:3d}: >>> {line}")
                            else:
                                print(f"  {i:3d}:     {line}")
            
            except Exception as e:
                print(f"\n⚠️  Error procesando evento: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    except Exception as e:
        print(f"\n⚠️  Error accediendo al calendario: {e}")
        import traceback
        traceback.print_exc()
        continue

print("\n" + "=" * 100)
print("✅ Análisis profundo completado")
print("=" * 100)
