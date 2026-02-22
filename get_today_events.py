#!/usr/bin/env python3
from calendar_client import iCloudCalendarClient
from config import load_env_file
from datetime import datetime

# Load environment variables
load_env_file()

# Initialize calendar client
calendar_client = iCloudCalendarClient()

# Get today's events
today = datetime.now()
events = calendar_client.get_today_events(target_date=today)

print(f"\n📅 EVENTOS DE HOY ({today.strftime('%d/%m/%Y')})")
print("=" * 60)

if not events:
    print("No hay eventos programados para hoy.")
else:
    for event in events:
        print(f"\n🔹 {event['summary']}")
        if event.get('all_day'):
            print(f"   ⏰ Todo el día")
        else:
            print(f"   ⏰ {event['start']} - {event['end']}")
        if event.get('location'):
            print(f"   📍 {event['location']}")
        if event.get('description'):
            print(f"   📝 {event['description']}")

print("\n" + "=" * 60)
print(f"Total: {len(events)} evento(s)")
