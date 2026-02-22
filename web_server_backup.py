"""
Web server for handling event copy requests and cronograma regeneration
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from calendar_client import iCloudCalendarClient
from events_db import mark_event_copied, mark_event_ignored, get_new_events
from firefly_client import FireflyClient
from datetime import datetime
import subprocess
import os
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for browser requests

# File to store Idealista data
IDEALISTA_DATA_FILE = 'idealista_data.json'

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/regenerate', methods=['POST', 'GET'])
def regenerate_endpoint():
    """Regenerate cronograma manually"""
    try:
        print("\n🔄 Manual regeneration requested...")
        new_cronograma_path = regenerate_cronograma()
        
        if new_cronograma_path:
            print(f"   ✅ Cronograma regenerated: {new_cronograma_path}")
            return jsonify({
                'success': True,
                'message': 'Cronograma regenerado exitosamente',
                'cronograma_path': new_cronograma_path
            })
        else:
            return jsonify({'error': 'Failed to regenerate cronograma'}), 500
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/copy-and-regenerate', methods=['POST'])
def copy_and_regenerate():
    """
    Copy an event from shared calendar to personal calendar
    and regenerate the cronograma
    """
    try:
        data = request.json
        event_uid = data.get('uid')
        
        if not event_uid:
            return jsonify({'error': 'UID is required'}), 400
        
        print(f"\n📋 Processing copy request for event UID: {event_uid}")
        
        # Initialize calendar client
        calendar_client = iCloudCalendarClient()
        
        if not calendar_client.client:
            return jsonify({'error': 'Calendar client not available'}), 500
        
        # Find the event in shared calendar
        print("   Searching for event in Casa Juana Doña...")
        source_event = find_event_by_uid(calendar_client, "Casa Juana Doña", event_uid)
        
        if not source_event:
            return jsonify({'error': 'Event not found in shared calendar'}), 404
        
        print(f"   ✓ Found event: {source_event['summary']}")
        
        # Copy event to personal calendar
        print("   Copying event to personal calendar...")
        success = copy_event_to_personal_calendar(calendar_client, source_event)
        
        if not success:
            return jsonify({'error': 'Failed to copy event'}), 500
        
        print("   ✓ Event copied successfully")
        
        # Mark event as copied in database
        mark_event_copied(event_uid)
        print("   ✓ Event marked as copied in database")
        
        # Regenerate cronograma
        print("   Regenerating cronograma...")
        new_cronograma_path = regenerate_cronograma()
        
        if new_cronograma_path:
            print(f"   ✓ Cronograma regenerated: {new_cronograma_path}")
            
            return jsonify({
                'success': True,
                'message': f'Evento "{source_event["summary"]}" copiado correctamente',
                'reload': True,
                'cronograma_path': new_cronograma_path
            })
        else:
            return jsonify({
                'success': True,
                'message': f'Evento "{source_event["summary"]}" copiado, pero no se pudo regenerar el cronograma',
                'reload': False
            })
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/ignore-event', methods=['POST'])
def ignore_event():
    """Mark an event as ignored"""
    try:
        data = request.json
        event_uid = data.get('uid')
        
        if not event_uid:
            return jsonify({'error': 'UID is required'}), 400
        
        mark_event_ignored(event_uid)
        
        return jsonify({
            'success': True,
            'message': 'Evento marcado como ignorado'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/new-events', methods=['GET'])
def get_new_events_api():
    """Get list of new events"""
    try:
        new_events = get_new_events()
        return jsonify({
            'success': True,
            'events': new_events
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/complete-task', methods=['POST'])
def complete_task():
    """
    Mark a task as completed in Todoist and regenerate cronograma
    """
    try:
        data = request.json
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({'error': 'task_id is required'}), 400
        
        print(f"\n✅ Completing task {task_id} in Todoist...")
        
        # Import Todoist client
        from todoist_client import TodoistClient
        from config import get_config
        
        config = get_config()
        todoist_client = TodoistClient(config['TODOIST_API_TOKEN'])
        
        # Complete the task
        success = todoist_client.complete_task(task_id)
        
        if not success:
            return jsonify({'error': 'Failed to complete task in Todoist'}), 500
        
        print("   ✅ Task completed in Todoist")
        
        # DO NOT regenerate cronograma - the visual mark will stay permanent
        # The task will disappear next time the cronograma is regenerated manually
        
        return jsonify({
            'success': True,
            'message': 'Tarea completada en Todoist'
        })
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/update-idealista', methods=['POST'])
def update_idealista():
    """
    Endpoint to receive Idealista data from Node-RED scraper
    """
    try:
        data = request.json
        
        if not data or 'properties' not in data:
            return jsonify({'error': 'Invalid data. "properties" field is required'}), 400
        
        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()
        data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        idealista_file = os.path.join(base_dir, IDEALISTA_DATA_FILE)
        
        # Load previous data for comparison
        previous_data = None
        if os.path.exists(idealista_file):
            try:
                with open(idealista_file, 'r', encoding='utf-8') as f:
                    previous_data = json.load(f)
            except:
                pass
        
        # Calculate changes for each property
        if previous_data and 'properties' in previous_data:
            prev_props = {p.get('propertyId'): p for p in previous_data.get('properties', [])}
            
            for prop in data['properties']:
                prop_id = prop.get('propertyId')
                if prop_id in prev_props:
                    prev = prev_props[prop_id]
                    prop['changes'] = {
                        'visitas': prop.get('visitas', 0) - prev.get('visitas', 0),
                        'favoritos': prop.get('favoritos', 0) - prev.get('favoritos', 0),
                        'mensajes': prop.get('mensajes', 0) - prev.get('mensajes', 0)
                    }
                else:
                    prop['changes'] = {'visitas': 0, 'favoritos': 0, 'mensajes': 0}
        else:
            # First time, no changes
            for prop in data['properties']:
                prop['changes'] = {'visitas': 0, 'favoritos': 0, 'mensajes': 0}
        
        # Save data to JSON file
        with open(idealista_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n🏠 Idealista data updated: {data}")
        
        return jsonify({
            'success': True,
            'message': 'Idealista data updated successfully',
            'properties_count': len(data['properties']),
            'timestamp': data['timestamp']
        })
    
    except Exception as e:
        print(f"   ❌ Error updating Idealista data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/idealista-data', methods=['GET'])
def get_idealista_data():
    """
    Get current Idealista data
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        idealista_file = os.path.join(base_dir, IDEALISTA_DATA_FILE)
        
        if os.path.exists(idealista_file):
            with open(idealista_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({
                'success': False,
                'message': 'No Idealista data available'
            }), 404
    
    except Exception as e:
        print(f"   ❌ Error getting Idealista data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/firefly-data', methods=['GET'])
def get_firefly_data():
    """
    Get Firefly III financial summary
    """
    try:
        print("\n💰 Fetching Firefly III data...")
        
        # Initialize Firefly client
        firefly_client = FireflyClient()
        
        # Get summary
        summary = firefly_client.get_summary()
        
        print(f"   ✅ Firefly data retrieved: Balance={summary['balance']['total']} {summary['balance']['currency']}")
        
        return jsonify({
            'success': True,
            'data': summary
        })
    
    except Exception as e:
        print(f"   ❌ Error getting Firefly data: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/week-calendar', methods=['GET'])
def get_week_calendar():
    """
    Get calendar events for the next 7 days
    """
    try:
        print("\n📅 Fetching week calendar events...")
        
        # Initialize calendar client
        calendar_client = iCloudCalendarClient()
        
        if not calendar_client.client:
            return jsonify({'error': 'Calendar client not available'}), 500
        
        # Get events for 7 days
        events_by_date = calendar_client.get_week_events(days=7)
        
        # Format events for JSON response
        formatted_events = {}
        for date_key, events in events_by_date.items():
            formatted_events[date_key] = [
                {
                    'summary': event['summary'],
                    'start': event['start'].strftime('%H:%M') if not event['all_day'] else 'Todo el día',
                    'end': event['end'].strftime('%H:%M') if not event['all_day'] else '',
                    'all_day': event['all_day']
                }
                for event in events
            ]
        
        print(f"   ✅ Found events in {len(formatted_events)} days")
        
        return jsonify({
            'success': True,
            'events': formatted_events,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        print(f"   ❌ Error getting week calendar: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/generate-cronograma', methods=['GET', 'POST'])
def generate_cronograma():
    """
    Endpoint para generar cronograma manualmente
    Útil para cron jobs externos (GitHub Actions, cron-job.org, etc.)
    """
    try:
        print("\n📅 Generando cronograma manualmente...")
        
        # Regenerar cronograma
        new_cronograma_path = regenerate_cronograma()
        
        if new_cronograma_path:
            print(f"   ✓ Cronograma generado: {new_cronograma_path}")
            
            return jsonify({
                'success': True,
                'message': 'Cronograma generado exitosamente',
                'cronograma_path': new_cronograma_path,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Error al generar cronograma'
            }), 500
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
@app.route('/cronograma', methods=['GET'])
def serve_cronograma():
    """Serve the latest cronograma HTML file"""
    import glob
    
    # Find the latest cronograma HTML file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pattern = os.path.join(base_dir, 'cronograma_v7_5_*.html')
    html_files = glob.glob(pattern)
    if not html_files:
        return jsonify({'error': 'No cronograma file found'}), 404
    
    latest_file = max(html_files, key=os.path.getmtime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}

def find_event_by_uid(calendar_client, calendar_name, uid):
    """Find an event by UID in a specific calendar"""
    try:
        from datetime import timedelta
        import pytz
        
        timezone = pytz.timezone('Europe/Madrid')
        today = datetime.now(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Search in next 60 days
        for days_ahead in range(60):
            current_date = today + timedelta(days=days_ahead)
            next_date = current_date + timedelta(days=1)
            
            events = calendar_client.get_events_from_calendar_range(
                calendar_name,
                current_date,
                next_date
            )
            
            for event in events:
                if event['uid'] == uid:
                    return event
        
        return None
    
    except Exception as e:
        print(f"Error finding event: {e}")
        return None

def copy_event_to_personal_calendar(calendar_client, source_event):
    """
    Copy an event to the personal calendar using CalDAV
    """
    try:
        print(f"   Copying event to personal calendar:")
        print(f"      Title: {source_event['summary']}")
        print(f"      Start: {source_event['start_datetime']}")
        print(f"      End: {source_event['end_datetime']}")
        
        # Create event in personal calendar ("Calendario")
        success = calendar_client.create_event(
            calendar_name="Calendario",
            summary=source_event['summary'],
            start_datetime=source_event['start_datetime'],
            end_datetime=source_event['end_datetime'],
            description=f"Copiado desde Casa Juana Doña el {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        
        return success
    
    except Exception as e:
        print(f"Error copying event: {e}")
        import traceback
        traceback.print_exc()
        return False

def regenerate_cronograma():
    """Regenerate the cronograma by running the generator script"""
    try:
        # Run the cronograma generator
        base_dir = os.path.dirname(os.path.abspath(__file__))
        result = subprocess.run(
            ['python3.11', 'cronograma_generator_v7_5.py'],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            # Find the latest generated cronograma
            import glob
            pattern = os.path.join(base_dir, 'cronograma_v7_5_*.html')
            cronogramas = glob.glob(pattern)
            if cronogramas:
                latest = max(cronogramas, key=os.path.getmtime)
                return latest
        else:
            print(f"Error regenerating cronograma: {result.stderr}")
            return None
    
    except Exception as e:
        print(f"Error regenerating cronograma: {e}")
        return None

if __name__ == '__main__':
    print("=" * 80)
    print("🌐 Starting Web Server")
    print("=" * 80)
    print("\nEndpoints:")
    print("  GET  /health                  - Health check")
    print("  POST /copy-and-regenerate     - Copy event and regenerate cronograma")
    print("  POST /ignore-event            - Mark event as ignored")
    print("  POST /complete-task           - Complete task in Todoist and regenerate")
    print("  GET  /new-events              - Get list of new events")
    print("  POST /update-idealista        - Update Idealista data from Node-RED")
    print("  GET  /idealista-data          - Get current Idealista data")
    print("  GET  /firefly-data            - Get Firefly III financial summary")
    print("\n" + "=" * 80)
    
    # Run server
    # Use PORT environment variable from Railway, default to 8000 for local development
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
