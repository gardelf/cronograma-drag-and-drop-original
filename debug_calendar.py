#!/usr/bin/env python3.11
"""
Debug script to see all calendars and events
"""

from calendar_client import iCloudCalendarClient
from datetime import datetime
from config import load_env_file

# Load environment variables
load_env_file()

# Create client
client = iCloudCalendarClient()

# Get today's events
print("\n" + "="*60)
print("TESTING get_today_events()")
print("="*60)
events = client.get_today_events()

print(f"\n📊 RESULTADO: {len(events)} eventos encontrados")
for i, event in enumerate(events, 1):
    print(f"\n{i}. {event['content']}")
    print(f"   Hora: {event['start_time']} - {event['end_time']}")
    print(f"   Duración: {event['duration']} min")
    print(f"   Prioridad: {event['priority']}")
    print(f"   Labels: {event['labels']}")
