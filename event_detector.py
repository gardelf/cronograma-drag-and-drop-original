"""
Detector for new events in shared calendar
"""

from calendar_client import iCloudCalendarClient
from events_db import add_new_event, get_all_known_uids
from datetime import datetime, timedelta
import pytz

def detect_new_events_in_shared_calendar(calendar_name="Casa Juana Doña", days_ahead=30):
    """
    Detect new events in the shared calendar that haven't been processed yet
    
    Args:
        calendar_name: Name of the shared calendar to monitor
        days_ahead: Number of days ahead to look for events
    
    Returns:
        List of new events detected
    """
    print(f"\n🔍 Detecting new events in '{calendar_name}'...")
    
    # Get calendar client
    client = iCloudCalendarClient()
    
    # Get events from shared calendar for the next N days
    timezone = pytz.timezone('Europe/Madrid')
    today = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = today + timedelta(days=days_ahead)
    
    print(f"   Searching from {today.date()} to {end_date.date()}")
    
    # Get all events from the shared calendar
    all_events = []
    current_date = today
    
    while current_date < end_date:
        next_date = current_date + timedelta(days=1)
        daily_events = client.get_events_from_calendar_range(
            calendar_name, 
            current_date, 
            next_date
        )
        all_events.extend(daily_events)
        current_date = next_date
    
    print(f"   Found {len(all_events)} total events in shared calendar")
    
    # Get all known UIDs from database
    known_uids = get_all_known_uids()
    print(f"   Known events in database: {len(known_uids)}")
    
    # Detect new events
    new_events = []
    for event in all_events:
        uid = event['uid']
        
        if uid not in known_uids:
            # This is a new event!
            new_events.append(event)
            
            # Add to database
            success = add_new_event(
                uid=uid,
                summary=event['summary'],
                start_time=event['start_time'],
                end_time=event['end_time'],
                date=event['date'],
                calendar_source=calendar_name
            )
            
            if success:
                print(f"   ✅ New event detected: {event['summary']} ({event['date']} {event['start_time']})")
            else:
                print(f"   ⚠️  Event already in DB: {event['summary']}")
    
    print(f"\n📊 Detection summary:")
    print(f"   Total events in calendar: {len(all_events)}")
    print(f"   New events detected: {len(new_events)}")
    
    return new_events

if __name__ == '__main__':
    # Test detection
    new_events = detect_new_events_in_shared_calendar()
    
    if new_events:
        print("\n🆕 New events found:")
        for event in new_events:
            print(f"   • {event['summary']} - {event['date']} {event['start_time']}-{event['end_time']}")
    else:
        print("\n✅ No new events detected")
