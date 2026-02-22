#!/usr/bin/env python3
"""
Script de diagnóstico para conexión CalDAV con iCloud
"""
from config import load_env_file
from datetime import datetime, timedelta
from caldav import DAVClient
from icalendar import Calendar
import pytz
import os

# Load environment variables
load_env_file()

username = os.getenv('ICLOUD_USERNAME')
password = os.getenv('ICLOUD_APP_PASSWORD')
caldav_url = "https://caldav.icloud.com/"
timezone = pytz.timezone('Europe/Madrid')

print("="*80)
print("🔍 DIAGNÓSTICO DE CONEXIÓN CALDAV CON iCLOUD")
print("="*80)

print(f"\n📋 Credenciales:")
print(f"   Usuario: {username}")
print(f"   Password configurado: {bool(password)}")
print(f"   URL CalDAV: {caldav_url}")

if not username or not password:
    print("\n❌ ERROR: Credenciales no configuradas")
    exit(1)

try:
    print("\n🔌 Intentando conectar con iCloud...")
    client = DAVClient(url=caldav_url, username=username, password=password)
    print("✅ Conexión establecida")
    
    print("\n📅 Obteniendo calendarios...")
    principal = client.principal()
    calendars = principal.calendars()
    
    print(f"✅ Encontrados {len(calendars)} calendarios:")
    for i, cal in enumerate(calendars, 1):
        print(f"   {i}. {cal.name}")
    
    # Buscar eventos de hoy
    today = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    print(f"\n🔍 Buscando eventos para HOY ({today.strftime('%d/%m/%Y')})...")
    print("="*80)
    
    total_events = 0
    for calendar in calendars:
        calendar_name = calendar.name
        print(f"\n📆 Calendario: {calendar_name}")
        print("-"*80)
        
        try:
            events = calendar.date_search(start=today, end=tomorrow, expand=True)
            events_list = list(events)
            
            if not events_list:
                print("   (sin eventos)")
                continue
            
            for event in events_list:
                try:
                    cal = Calendar.from_ical(event.data)
                    
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            summary = str(component.get('summary', 'Sin título'))
                            dtstart = component.get('dtstart')
                            dtend = component.get('dtend')
                            
                            if dtstart:
                                # Check if all-day or timed event
                                if hasattr(dtstart.dt, 'hour'):
                                    # Timed event
                                    start_dt = dtstart.dt
                                    if start_dt.tzinfo is None:
                                        start_dt = timezone.localize(start_dt)
                                    else:
                                        start_dt = start_dt.astimezone(timezone)
                                    
                                    if dtend:
                                        end_dt = dtend.dt
                                        if end_dt.tzinfo is None:
                                            end_dt = timezone.localize(end_dt)
                                        else:
                                            end_dt = end_dt.astimezone(timezone)
                                    else:
                                        end_dt = start_dt + timedelta(hours=1)
                                    
                                    print(f"   ✓ {start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')}: {summary}")
                                    total_events += 1
                                else:
                                    # All-day event
                                    print(f"   ✓ TODO EL DÍA: {summary}")
                                    total_events += 1
                
                except Exception as e:
                    print(f"   ⚠️  Error procesando evento: {e}")
        
        except Exception as e:
            print(f"   ❌ Error accediendo al calendario: {e}")
    
    print("\n" + "="*80)
    print(f"📊 TOTAL DE EVENTOS ENCONTRADOS: {total_events}")
    print("="*80)

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
