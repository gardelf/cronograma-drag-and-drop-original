"""
Script to analyze UIDs across multiple dates
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

print("=" * 100)
print("🔍 ANÁLISIS DE UIDs EN MÚLTIPLES FECHAS")
print("=" * 100)

# Define date ranges to search
today = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
date_ranges = [
    ("Ayer", today - timedelta(days=1), today),
    ("Hoy", today, today + timedelta(days=1)),
    ("Mañana", today + timedelta(days=1), today + timedelta(days=2)),
    ("En 7 días", today + timedelta(days=7), today + timedelta(days=8)),
    ("En 14 días", today + timedelta(days=14), today + timedelta(days=15)),
    ("Próximos 30 días", today, today + timedelta(days=30)),
]

all_events = {}

for label, start_date, end_date in date_ranges:
    print(f"\n{'=' * 100}")
    print(f"📅 {label}: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
    print(f"{'=' * 100}")
    
    events_found = 0
    
    for calendar in calendars:
        calendar_name = calendar.name
        
        try:
            events = calendar.date_search(start=start_date, end=end_date, expand=True)
            
            for event in events:
                try:
                    cal = Calendar.from_ical(event.data)
                    
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            summary = str(component.get('summary', 'Sin título'))
                            uid = str(component.get('uid', 'N/A'))
                            dtstart = component.get('dtstart').dt
                            
                            if isinstance(dtstart, datetime):
                                start_dt = dtstart.astimezone(timezone)
                                event_date = start_dt.strftime('%d/%m/%Y')
                                event_time = start_dt.strftime('%H:%M')
                            else:
                                event_date = dtstart.strftime('%d/%m/%Y')
                                event_time = "Todo el día"
                            
                            # Store event info
                            event_key = f"{event_date}_{summary}"
                            if event_key not in all_events:
                                all_events[event_key] = []
                            
                            all_events[event_key].append({
                                'summary': summary,
                                'uid': uid,
                                'date': event_date,
                                'time': event_time,
                                'calendar': calendar_name,
                                'search_range': label
                            })
                            
                            print(f"  📌 {event_date} {event_time} - {summary}")
                            print(f"     UID: {uid}")
                            print(f"     Calendario: {calendar_name}")
                            events_found += 1
                
                except Exception as e:
                    continue
        
        except Exception as e:
            continue
    
    if events_found == 0:
        print("  ℹ️  No se encontraron eventos en este rango")

# Analyze patterns
print("\n" + "=" * 100)
print("📊 ANÁLISIS DE PATRONES")
print("=" * 100)

# Check for recurring events (same title, different dates, same or different UID)
print("\n🔄 Eventos recurrentes (mismo título en diferentes fechas):")
title_groups = {}
for event_key, event_list in all_events.items():
    for event in event_list:
        title = event['summary']
        if title not in title_groups:
            title_groups[title] = []
        title_groups[title].append(event)

recurring_found = False
for title, events in title_groups.items():
    if len(events) > 1:
        recurring_found = True
        print(f"\n  📌 '{title}' aparece {len(events)} veces:")
        unique_uids = set([e['uid'] for e in events])
        
        if len(unique_uids) == 1:
            print(f"     ✅ MISMO UID en todas las ocurrencias: {list(unique_uids)[0]}")
        else:
            print(f"     ⚠️  DIFERENTES UIDs:")
        
        for event in sorted(events, key=lambda x: x['date']):
            print(f"       • {event['date']} {event['time']} - UID: {event['uid']}")

if not recurring_found:
    print("  ℹ️  No se encontraron eventos recurrentes en el período analizado")

# UID format analysis
print("\n🔑 Análisis de formato de UIDs:")
all_uids = [event['uid'] for events in all_events.values() for event in events]
if all_uids:
    print(f"  • Total de UIDs encontrados: {len(all_uids)}")
    print(f"  • UIDs únicos: {len(set(all_uids))}")
    print(f"\n  Ejemplos de UIDs:")
    for uid in list(set(all_uids))[:5]:
        print(f"    - {uid}")
        # Analyze format
        if '-' in uid:
            parts = uid.split('-')
            print(f"      Formato: {len(parts)} partes separadas por guiones")
            print(f"      Longitudes: {[len(p) for p in parts]}")

print("\n" + "=" * 100)
print("✅ Análisis completado")
print("=" * 100)
