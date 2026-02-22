"""
Manual test script - runs the full agenda generation without server
"""

from config import get_config
from todoist_client import TodoistClient
from chatgpt_processor import ChatGPTProcessor
from email_sender import EmailSender
from datetime import datetime


def main():
    print("="*60)
    print("📅 DAILY AGENDA AUTOMATION - MANUAL TEST")
    print("="*60)
    
    # Load configuration
    config = get_config()
    
    # Initialize clients
    print("\n1️⃣ Initializing clients...")
    todoist_client = TodoistClient(config['TODOIST_API_TOKEN'])
    chatgpt_processor = ChatGPTProcessor(config['OPENAI_API_KEY'])
    email_sender = EmailSender(
        smtp_server=config['SMTP_SERVER'],
        smtp_port=config['SMTP_PORT'],
        username=config['SMTP_USERNAME'],
        password=config['SMTP_PASSWORD']
    )
    print("✅ Clients initialized")
    
    # Get tasks from Todoist
    print("\n2️⃣ Fetching tasks from Todoist...")
    todoist_tasks = todoist_client.get_today_tasks()
    formatted_tasks = todoist_client.format_tasks_for_display(todoist_tasks)
    print(f"✅ Found {len(formatted_tasks)} tasks for today:")
    for task in formatted_tasks:
        print(f"   - {task['content']} (Priority: {task['priority']})")
    
    # Simulate calendar events (since we're using iPhone shortcuts method)
    print("\n3️⃣ Using sample calendar events for testing...")
    calendar_events = [
        {
            "title": "Reunión de prueba",
            "start_time": "10:00",
            "location": "Oficina"
        },
        {
            "title": "Comida",
            "start_time": "14:00",
            "location": ""
        }
    ]
    print(f"✅ Using {len(calendar_events)} sample calendar events")
    
    # Process with ChatGPT
    print("\n4️⃣ Processing with ChatGPT...")
    print("   (This may take 10-20 seconds...)")
    agenda_html = chatgpt_processor.create_agenda_table(calendar_events, formatted_tasks)
    print("✅ Agenda generated successfully")
    print(f"   HTML length: {len(agenda_html)} characters")
    
    # Save HTML to file
    output_file = f"/home/ubuntu/daily-agenda-automation/agenda_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(agenda_html)
    print(f"✅ Agenda saved to: {output_file}")
    
    # Try to send email (will fail if SMTP not configured, but that's OK for testing)
    print("\n5️⃣ Attempting to send email...")
    if config['SMTP_USERNAME'] and config['SMTP_PASSWORD']:
        email_sent = email_sender.send_agenda(config['RECIPIENT_EMAIL'], agenda_html)
        if email_sent:
            print(f"✅ Email sent successfully to {config['RECIPIENT_EMAIL']}")
        else:
            print("❌ Email sending failed")
    else:
        print("⚠️  SMTP not configured - skipping email send")
        print(f"   Email would be sent to: {config['RECIPIENT_EMAIL']}")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"\nYou can view the generated agenda at:")
    print(f"  {output_file}")
    print("\nTo view it, open the file in a web browser.")


if __name__ == "__main__":
    main()
