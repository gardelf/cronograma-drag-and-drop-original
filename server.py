"""
Main Server
Flask server to receive calendar data from iPhone and process daily agenda
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json

from config import get_config
from todoist_client import TodoistClient
from chatgpt_processor import ChatGPTProcessor
from email_sender import EmailSender


app = Flask(__name__)

# Load configuration
config = get_config()

# Initialize clients
todoist_client = TodoistClient(config['TODOIST_API_TOKEN'])
chatgpt_processor = ChatGPTProcessor(config['OPENAI_API_KEY'])
email_sender = EmailSender(
    smtp_server=config['SMTP_SERVER'],
    smtp_port=config['SMTP_PORT'],
    username=config['SMTP_USERNAME'],
    password=config['SMTP_PASSWORD']
)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "service": "Daily Agenda Automation"
    })


@app.route('/process-agenda', methods=['POST'])
def process_agenda():
    """
    Main endpoint to process daily agenda
    Receives calendar events from iPhone and processes with Todoist tasks
    """
    try:
        # Verify secret token for security
        auth_header = request.headers.get('Authorization')
        if auth_header != f"Bearer {config['SECRET_TOKEN']}":
            return jsonify({"error": "Unauthorized"}), 401
        
        # Get calendar events from request
        data = request.get_json()
        calendar_events = data.get('events', [])
        
        print(f"📅 Received {len(calendar_events)} calendar events")
        
        # Get tasks from Todoist
        print("📋 Fetching tasks from Todoist...")
        todoist_tasks = todoist_client.get_today_tasks()
        formatted_tasks = todoist_client.format_tasks_for_display(todoist_tasks)
        print(f"✅ Found {len(formatted_tasks)} tasks")
        
        # Process with ChatGPT
        print("🤖 Processing with ChatGPT...")
        agenda_html = chatgpt_processor.create_agenda_table(calendar_events, formatted_tasks)
        print("✅ Agenda generated")
        
        # Send via email
        print(f"📧 Sending email to {config['RECIPIENT_EMAIL']}...")
        email_sent = email_sender.send_agenda(config['RECIPIENT_EMAIL'], agenda_html)
        
        if email_sent:
            return jsonify({
                "status": "success",
                "message": "Agenda processed and sent successfully",
                "events_count": len(calendar_events),
                "tasks_count": len(formatted_tasks),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "partial_success",
                "message": "Agenda processed but email not sent (check SMTP configuration)",
                "events_count": len(calendar_events),
                "tasks_count": len(formatted_tasks),
                "agenda_preview": agenda_html[:500],
                "timestamp": datetime.now().isoformat()
            })
    
    except Exception as e:
        print(f"❌ Error processing agenda: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/test-todoist', methods=['GET'])
def test_todoist():
    """Test endpoint to verify Todoist connection"""
    try:
        tasks = todoist_client.get_today_tasks()
        formatted = todoist_client.format_tasks_for_display(tasks)
        
        return jsonify({
            "status": "success",
            "tasks_count": len(formatted),
            "tasks": [{"content": t['content'], "priority": t['priority']} for t in formatted]
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/test-email', methods=['GET'])
def test_email():
    """Test endpoint to verify email sending"""
    try:
        test_html = """
        <html>
        <body>
            <h1>✅ Email Test Successful</h1>
            <p>Your Daily Agenda Automation system is working correctly!</p>
            <p>Timestamp: {}</p>
        </body>
        </html>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        success = email_sender.send_agenda(
            config['RECIPIENT_EMAIL'],
            test_html,
            "Test Email - Daily Agenda System"
        )
        
        return jsonify({
            "status": "success" if success else "failed",
            "recipient": config['RECIPIENT_EMAIL'],
            "smtp_configured": bool(config['SMTP_USERNAME'])
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/manual-run', methods=['GET'])
def manual_run():
    """
    Manual trigger endpoint - processes agenda without calendar events
    Useful for testing or manual execution
    """
    try:
        # Get tasks from Todoist
        print("📋 Fetching tasks from Todoist...")
        todoist_tasks = todoist_client.get_today_tasks()
        formatted_tasks = todoist_client.format_tasks_for_display(todoist_tasks)
        
        # Use empty calendar events for manual run
        calendar_events = []
        
        # Process with ChatGPT
        print("🤖 Processing with ChatGPT...")
        agenda_html = chatgpt_processor.create_agenda_table(calendar_events, formatted_tasks)
        
        # Send via email
        print(f"📧 Sending email to {config['RECIPIENT_EMAIL']}...")
        email_sent = email_sender.send_agenda(config['RECIPIENT_EMAIL'], agenda_html)
        
        return jsonify({
            "status": "success",
            "message": "Manual run completed",
            "tasks_count": len(formatted_tasks),
            "email_sent": email_sent,
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    port = config['PORT']
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║   📅 Daily Agenda Automation Server                       ║
    ║                                                            ║
    ║   Server running on port {port}                               ║
    ║                                                            ║
    ║   Endpoints:                                               ║
    ║   - GET  /health          Health check                     ║
    ║   - POST /process-agenda  Process daily agenda             ║
    ║   - GET  /test-todoist    Test Todoist connection          ║
    ║   - GET  /test-email      Test email sending               ║
    ║   - GET  /manual-run      Manual agenda generation         ║
    ║                                                            ║
    ║   Secret Token: {config['SECRET_TOKEN'][:20]}...                ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    app.run(host='0.0.0.0', port=port, debug=True)
