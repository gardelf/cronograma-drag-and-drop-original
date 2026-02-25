"""
Web server for handling event copy requests and cronograma regeneration
"""

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from calendar_client import iCloudCalendarClient
from events_db import mark_event_copied, mark_event_ignored, get_new_events
from firefly_client import FireflyClient
from datetime import datetime
import subprocess
import os
import json

# Import expense utilities
from expense_utils import (
    categorizar_gasto,
    registrar_en_firefly,
    extraer_monto_descripcion,
    CATEGORIAS_CONOCIDAS,
    registrar_presupuesto
)

app = Flask(__name__)
CORS(app)  # Enable CORS for browser requests

# File to store Idealista data
IDEALISTA_DATA_FILE = 'idealista_data.json'

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

@app.route('/boe-subastas', methods=['GET'])
def boe_dashboard():
    """BOE Subastas Dashboard"""
    return render_template('boe-dashboard.html')

@app.route('/debug/firefly', methods=['GET'])
def debug_firefly():
    """Debug endpoint for Firefly III connection"""
    try:
        import os
        from config import load_env_file
        
        # Load .env if exists
        load_env_file()
        
        firefly_url = os.getenv('FIREFLY_URL')
        firefly_token = os.getenv('FIREFLY_TOKEN', '')
        
        icloud_username = os.getenv('ICLOUD_USERNAME')
        icloud_password = os.getenv('ICLOUD_APP_PASSWORD')
        
        debug_info = {
            'env_vars': {
                'FIREFLY_URL': firefly_url,
                'FIREFLY_TOKEN_exists': bool(firefly_token),
                'FIREFLY_TOKEN_length': len(firefly_token),
                'FIREFLY_TOKEN_first_20': firefly_token[:20] if firefly_token else None,
                'ICLOUD_USERNAME': icloud_username,
                'ICLOUD_APP_PASSWORD_exists': bool(icloud_password),
                'ICLOUD_APP_PASSWORD_length': len(icloud_password) if icloud_password else 0
            }
        }
        
        # Try to connect to Firefly
        try:
            client = FireflyClient()
            debug_info['client_token_length'] = len(client.token)
            debug_info['client_url'] = client.base_url
            
            # Try to get monthly summary directly
            from datetime import datetime
            november_data = client.get_monthly_summary(2025, 11)
            debug_info['november_raw'] = november_data
            
            # Try direct API call
            import requests
            try:
                direct_url = f"{firefly_url}/api/v1/transactions?start=2025-11-01&end=2025-11-30&limit=3"
                direct_response = requests.get(
                    direct_url,
                    headers={
                        'Authorization': f'Bearer {firefly_token}',
                        'Accept': 'application/json'
                    },
                    timeout=10
                )
                debug_info['direct_api'] = {
                    'status_code': direct_response.status_code,
                    'data_count': len(direct_response.json().get('data', [])) if direct_response.status_code == 200 else 0,
                    'url': direct_url
                }
            except Exception as api_e:
                debug_info['direct_api'] = {'error': str(api_e)}
            
            summary = client.get_summary()
            debug_info['connection'] = 'SUCCESS'
            debug_info['summary_keys'] = list(summary.keys()) if summary else None
            debug_info['data'] = {
                'current_month_expenses': summary.get('current_month', {}).get('expenses', 0),
                'previous_month_expenses': summary.get('previous_month', {}).get('expenses', 0),
                'weekly_expenses': summary.get('weekly', {}).get('expenses', 0)
            }
        except Exception as e:
            debug_info['connection'] = 'FAILED'
            debug_info['error'] = str(e)
            import traceback
            debug_info['traceback'] = traceback.format_exc()
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/files', methods=['GET'])
def debug_files():
    """Debug endpoint to list cronograma files"""
    import glob
    from datetime import datetime as dt
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    pattern = os.path.join(base_dir, 'cronograma_v7_5_*.html')
    html_files = glob.glob(pattern)
    
    files_info = []
    for f in sorted(html_files, key=os.path.getmtime, reverse=True):
        mtime = os.path.getmtime(f)
        mtime_str = dt.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        files_info.append({
            'filename': os.path.basename(f),
            'mtime': mtime_str,
            'size': os.path.getsize(f)
        })
    
    latest = max(html_files, key=os.path.getmtime) if html_files else None
    
    return jsonify({
        'base_dir': base_dir,
        'pattern': pattern,
        'files_count': len(html_files),
        'files': files_info,
        'latest_file': os.path.basename(latest) if latest else None
    })

@app.route('/debug/calendar', methods=['GET'])
def debug_calendar():
    """Debug endpoint for calendar connection"""
    try:
        import os
        from config import load_env_file
        from datetime import datetime
        
        # Load .env if exists
        load_env_file()
        
        icloud_username = os.getenv('ICLOUD_USERNAME')
        icloud_password = os.getenv('ICLOUD_APP_PASSWORD')
        
        debug_info = {
            'env_vars': {
                'ICLOUD_USERNAME': icloud_username,
                'ICLOUD_APP_PASSWORD_exists': bool(icloud_password),
                'ICLOUD_APP_PASSWORD_length': len(icloud_password) if icloud_password else 0
            }
        }
        
        # Try to get today's events
        try:
            calendar_client = iCloudCalendarClient()
            debug_info['client_created'] = calendar_client.client is not None
            
            if calendar_client.client:
                events = calendar_client.get_today_events()
                debug_info['connection'] = 'SUCCESS'
                debug_info['events_count'] = len(events)
                debug_info['events'] = events
            else:
                debug_info['connection'] = 'FAILED'
                debug_info['error'] = 'Client is None - credentials not configured'
        except Exception as e:
            debug_info['connection'] = 'FAILED'
            debug_info['error'] = str(e)
            import traceback
            debug_info['traceback'] = traceback.format_exc()
        
        return jsonify(debug_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/todoist', methods=['GET'])
def debug_todoist():
    """Debug endpoint for Todoist connection"""
    try:
        import os
        from config import load_env_file, get_config
        from todoist_client import TodoistClient
        import requests
        
        # Load .env if exists
        load_env_file()
        config = get_config()
        
        todoist_token = config.get('TODOIST_API_TOKEN', '')
        
        debug_info = {
            'env_vars': {
                'TODOIST_API_TOKEN_exists': bool(todoist_token),
                'TODOIST_API_TOKEN_length': len(todoist_token),
                'TODOIST_API_TOKEN_first_10': todoist_token[:10] if todoist_token else None,
                'TODOIST_API_TOKEN_last_10': todoist_token[-10:] if todoist_token else None,
            }
        }
        
        if not todoist_token:
            debug_info['error'] = 'TODOIST_API_TOKEN not configured'
            return jsonify(debug_info), 500
        
        # Test direct API call
        try:
            url = "https://api.todoist.com/api/v1/tasks"
            headers = {
                "Authorization": f"Bearer {todoist_token}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            debug_info['direct_api'] = {
                'url': url,
                'status_code': response.status_code,
                'response_preview': response.text[:200] if response.text else None
            }
            
            if response.status_code == 200:
                data = response.json()
                tasks = data.get('results', data) if isinstance(data, dict) else data
                debug_info['direct_api']['tasks_count'] = len(tasks) if isinstance(tasks, list) else 0
                debug_info['direct_api']['response_type'] = type(data).__name__
                debug_info['direct_api']['has_results_key'] = 'results' in data if isinstance(data, dict) else False
                
                if isinstance(tasks, list) and len(tasks) > 0:
                    debug_info['direct_api']['first_task'] = {
                        'id': tasks[0].get('id'),
                        'content': tasks[0].get('content'),
                        'priority': tasks[0].get('priority')
                    }
            
        except Exception as api_e:
            debug_info['direct_api'] = {'error': str(api_e)}
        
        # Test with TodoistClient
        try:
            client = TodoistClient(todoist_token)
            debug_info['client'] = {
                'base_url': client.BASE_URL
            }
            
            all_tasks = client.get_all_active_tasks()
            debug_info['client']['all_tasks_count'] = len(all_tasks)
            
            formatted_tasks = client.format_tasks_for_display(all_tasks)
            debug_info['client']['formatted_tasks_count'] = len(formatted_tasks)
            
            if len(formatted_tasks) > 0:
                debug_info['client']['first_formatted_task'] = {
                    'id': formatted_tasks[0].get('id'),
                    'content': formatted_tasks[0].get('content'),
                    'priority': formatted_tasks[0].get('priority'),
                    'due_date': formatted_tasks[0].get('due_date')
                }
            
            # Filter tasks for today
            from datetime import datetime
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            today_tasks = []
            for task in formatted_tasks:
                due_date = task.get('due_date')
                if due_date is None or due_date <= today_str:
                    today_tasks.append(task)
            
            debug_info['client']['today_tasks_count'] = len(today_tasks)
            
        except Exception as client_e:
            debug_info['client'] = {'error': str(client_e)}
            import traceback
            debug_info['client']['traceback'] = traceback.format_exc()
        
        return jsonify(debug_info)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

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
    Mark a task as completed in Todoist and save to local database
    """
    try:
        data = request.json
        task_id = data.get('task_id')
        content = data.get('content', '')
        start_time = data.get('start_time', '')
        end_time = data.get('end_time', '')
        priority = data.get('priority', 'P4')
        labels = data.get('labels', [])
        
        if not task_id:
            return jsonify({'error': 'task_id is required'}), 400
        
        print(f"\n✅ Completing task {task_id} in Todoist...")
        print(f"   📋 Task: {content}")
        print(f"   ⏰ Time: {start_time}-{end_time}")
        
        # Import Todoist client
        from todoist_client import TodoistClient
        from config import get_config
        
        config = get_config()
        todoist_client = TodoistClient(config['TODOIST_API_TOKEN'])
        
        # Complete the task in Todoist
        success = todoist_client.complete_task(task_id)
        
        if not success:
            return jsonify({'error': 'Failed to complete task in Todoist'}), 500
        
        print("   ✅ Task completed in Todoist")
        
        # Save to local database
        from completed_tasks_db import save_completed_task
        
        save_completed_task(
            task_id=task_id,
            content=content,
            start_time=start_time,
            end_time=end_time,
            priority=priority,
            labels=labels
        )
        
        print("   ✅ Task saved to local completed tasks database")
        
        return jsonify({
            'success': True,
            'message': 'Tarea completada y guardada localmente'
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
        from idealista_postgres import save_idealista_data, get_idealista_data
        
        data = request.json
        
        if not data or 'properties' not in data:
            return jsonify({'error': 'Invalid data. "properties" field is required'}), 400
        
        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()
        data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Load previous data for comparison
        previous_data = get_idealista_data()
        
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
        
        # Save data to PostgreSQL database
        print(f"\n🔍 DEBUG: Saving Idealista data to PostgreSQL...")
        print(f"🔍 DEBUG: Data to save: {data}")
        save_idealista_data(data)
        print(f"\n✅ Idealista data saved to PostgreSQL")
        
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
        from idealista_postgres import get_idealista_data as load_idealista
        
        print("🔍 DEBUG: Loading Idealista data...")
        data = load_idealista()
        print(f"🔍 DEBUG: Data loaded: {data}")
        print(f"🔍 DEBUG: Properties count: {len(data.get('properties', []))}")
        
        if data and data.get('properties'):
            return jsonify(data)
        else:
            return jsonify({
                'success': False,
                'message': 'No Idealista data available',
                'debug_data': data
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

@app.route('/calendar-demos', methods=['GET'])
def calendar_demos():
    """
    Show calendar demos page
    """
    try:
        return send_file('templates/calendar_demos.html')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
            formatted_events[date_key] = []
            for event in events:
                if event['all_day']:
                    formatted_event = {
                        'summary': event['summary'],
                        'start': 'Todo el día',
                        'end': '',
                        'all_day': True
                    }
                else:
                    # Check if event spans multiple days
                    start_date = event['start'].date()
                    end_date = event['end'].date()
                    
                    if start_date == end_date:
                        # Same day event - show only times
                        formatted_event = {
                            'summary': event['summary'],
                            'start': event['start'].strftime('%H:%M'),
                            'end': event['end'].strftime('%H:%M'),
                            'all_day': False
                        }
                    else:
                        # Multi-day event - show end date + time
                        # weekday() returns 0=Monday, 6=Sunday
                        days_of_week = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
                        end_day_name = days_of_week[event['end'].weekday()]
                        formatted_event = {
                            'summary': event['summary'],
                            'start': event['start'].strftime('%H:%M'),
                            'end': f"{end_day_name} {event['end'].strftime('%H:%M')}",
                            'all_day': False,
                            'multi_day': True
                        }
                
                formatted_events[date_key].append(formatted_event)
        
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

# ============================================================================
# EXPENSE API ENDPOINTS (Voice-based expense tracking)
# ============================================================================

@app.route('/registrar-gasto', methods=['POST'])
def registrar_gasto():
    """
    Endpoint para registrar un gasto por voz
    
    Body JSON:
    {
        "texto": "25.50 Mercadona"
    }
    
    O alternativamente:
    {
        "monto": 25.50,
        "descripcion": "Mercadona"
    }
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No se recibieron datos'
            }), 400
        
        fecha_gasto = None
        categoria_manual = None
        tags_gasto = []
        
        # Opción 1: Texto completo (desde Siri)
        if 'texto' in data:
            texto = data['texto']
            resultado_extraccion = extraer_monto_descripcion(texto)
            
            # Manejar ambos casos: con o sin tags
            if len(resultado_extraccion) == 5:
                monto, descripcion, fecha_gasto, categoria_manual, tags_gasto = resultado_extraccion
            else:
                monto, descripcion, fecha_gasto, categoria_manual = resultado_extraccion
                tags_gasto = []
            
            # Validar que si hay tag "extraordinario", debe haber fecha
            if 'Extraordinario' in tags_gasto and fecha_gasto is None:
                return jsonify({
                    'success': False,
                    'error': 'Los gastos extraordinarios DEBEN incluir fecha. Ejemplo: "500 viaje extraordinario 15 febrero"'
                }), 400
            
            if monto is None or descripcion is None:
                return jsonify({
                    'success': False,
                    'error': 'No se pudo extraer monto y descripción del texto. Formato esperado: "25.50 Mercadona"'
                }), 400
        
        # Opción 2: Monto y descripción separados
        elif 'monto' in data and 'descripcion' in data:
            monto = float(data['monto'])
            descripcion = data['descripcion']
            fecha_gasto = data.get('fecha')  # Opcional
            categoria_manual = data.get('categoria')  # Opcional
            tags_gasto = data.get('tags', [])  # Opcional
        
        else:
            return jsonify({
                'success': False,
                'error': 'Faltan datos. Envía "texto" o "monto" + "descripcion"'
            }), 400
        
        print(f"\n💰 Registrando gasto: {monto} EUR - {descripcion}")
        if fecha_gasto:
            print(f"   📅 Fecha: {fecha_gasto}")
        if tags_gasto:
            print(f"   🏷️  Tags: {', '.join(tags_gasto)}")
        
        # Agregar tag a la descripción si existe
        descripcion_con_tag = descripcion
        if 'Extraordinario' in tags_gasto:
            descripcion_con_tag = f"{descripcion} [EXTRAORDINARIO]"
        
        # Categorizar (usar categoría manual si existe, sino categorizar automáticamente)
        if categoria_manual:
            categoria = categoria_manual
            metodo = 'manual'
            print(f"   📁 Categoría manual: {categoria}")
        else:
            categoria, metodo = categorizar_gasto(descripcion)
            print(f"   📁 Categoría automática: {categoria} (método: {metodo})")
        
        # Registrar en Firefly III con tags
        exito, resultado = registrar_en_firefly(monto, descripcion_con_tag, categoria, fecha_gasto, tags_gasto)
        
        if exito:
            print(f"   ✅ Registrado en Firefly III")
            mensaje = f"Registrado: {monto} euros en {categoria}"
            if fecha_gasto:
                mensaje += f" (fecha: {fecha_gasto})"
            
            return jsonify({
                'success': True,
                'monto': monto,
                'descripcion': descripcion,
                'categoria': categoria,
                'fecha': fecha_gasto,
                'tags': tags_gasto,
                'metodo_categorizacion': metodo,
                'mensaje': mensaje,
                'firefly_response': resultado
            })
        else:
            print(f"   ❌ Error: {resultado}")
            return jsonify({
                'success': False,
                'error': f'Error al registrar en Firefly III: {resultado}'
            }), 500
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/categorias', methods=['GET'])
def listar_categorias():
    """Lista las categorías disponibles"""
    return jsonify({
        'categorias': list(CATEGORIAS_CONOCIDAS.keys())
    })

@app.route('/gastos-ayer', methods=['GET'])
def gastos_ayer():
    """
    Endpoint para obtener gastos del día anterior
    Para usar en notificaciones o widgets de iPhone
    
    Devuelve:
    {
        "date": "2025-12-17",
        "total": 45.50,
        "count": 5,
        "currency": "EUR",
        "expenses": [
            {"description": "Mercadona", "amount": 25.50, "category": "Comida"},
            ...
        ],
        "summary": "Ayer gastaste 45.50 EUR en 5 compras"
    }
    """
    try:
        firefly_client = FireflyClient()
        data = firefly_client.get_yesterday_expenses()
        
        # Crear resumen en texto para notificación
        if data['count'] == 0:
            summary = "Ayer no hubo gastos registrados"
        else:
            summary = f"Ayer gastaste {data['total']} {data['currency']} en {data['count']} compras:\n"
            for expense in data['expenses']:
                summary += f"- {expense['description']}: {expense['amount']} {expense['currency']} ({expense['category']})\n"
        
        data['summary'] = summary.strip()
        
        return jsonify(data)
        
    except Exception as e:
        print(f"❌ Error obteniendo gastos de ayer: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': str(e),
            'date': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'total': 0,
            'count': 0,
            'expenses': [],
            'summary': 'Error al obtener gastos de ayer'
        }), 500

@app.route('/gastos-ayer-html', methods=['GET'])
def gastos_ayer_html():
    """
    Endpoint para obtener gastos del día anterior en formato HTML
    Para mostrar en Vista Rápida desde el atajo de iPhone
    """
    try:
        firefly_client = FireflyClient()
        data = firefly_client.get_yesterday_expenses()
        
        # Mapeo de categorías a emojis
        category_emojis = {
            "Comida": "🍽️",
            "Coche": "🚗",
            "Salud": "💊",
            "Transporte": "🚌",
            "Ocio": "🎮",
            "Ropa": "👕",
            "Casa": "🏠",
            "Tecnología": "💻",
            "Viajes": "✈️",
            "Otros": "📦"
        }
        
        # Generar HTML
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gastos de Ayer</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 28px;
            color: #333;
            margin-bottom: 10px;
        }}
        .header .date {{
            color: #666;
            font-size: 14px;
        }}
        .total-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }}
        .total-box .amount {{
            font-size: 48px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .total-box .label {{
            font-size: 16px;
            opacity: 0.9;
        }}
        .expenses-list {{
            margin-top: 20px;
        }}
        .expense-item {{
            display: flex;
            align-items: center;
            padding: 15px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 12px;
            transition: transform 0.2s;
        }}
        .expense-item:hover {{
            transform: translateX(5px);
        }}
        .expense-emoji {{
            font-size: 32px;
            margin-right: 15px;
        }}
        .expense-details {{
            flex: 1;
        }}
        .expense-description {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin-bottom: 3px;
        }}
        .expense-category {{
            font-size: 13px;
            color: #666;
        }}
        .expense-amount {{
            font-size: 20px;
            font-weight: bold;
            color: #667eea;
        }}
        .no-expenses {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        .no-expenses .emoji {{
            font-size: 64px;
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 Gastos de Ayer</h1>
            <div class="date">📅 {data['date']}</div>
        </div>
        """
        
        if data['count'] == 0:
            html += """
        <div class="no-expenses">
            <div class="emoji">✅</div>
            <h2>Sin gastos registrados</h2>
            <p>¡Buen trabajo!</p>
        </div>
            """
        else:
            html += f"""
        <div class="total-box">
            <div class="amount">{data['total']:.2f} {data['currency']}</div>
            <div class="label">en {data['count']} {'compra' if data['count'] == 1 else 'compras'}</div>
        </div>
        
        <div class="expenses-list">
            """
            
            for expense in data['expenses']:
                emoji = category_emojis.get(expense['category'], '💰')
                description = expense['description'].replace('€', '').strip()
                html += f"""
            <div class="expense-item">
                <div class="expense-emoji">{emoji}</div>
                <div class="expense-details">
                    <div class="expense-description">{description}</div>
                    <div class="expense-category">{expense['category']}</div>
                </div>
                <div class="expense-amount">{expense['amount']:.2f}€</div>
            </div>
                """
            
            html += """
        </div>
            """
        
        html += """
    </div>
</body>
</html>
        """
        
        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
    
    except Exception as e:
        print(f"Error en gastos-ayer-html: {e}")
        import traceback
        traceback.print_exc()
        
        error_html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 20px;
            text-align: center;
        }}
        .error {{
            color: #e74c3c;
            font-size: 48px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="error">❌</div>
    <h2>Error al obtener gastos</h2>
    <p>{str(e)}</p>
</body>
</html>
        """
        return error_html, 500, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/registrar-presupuesto', methods=['POST'])
def registrar_presupuesto_endpoint():
    """
    Endpoint para registrar un presupuesto por voz
    
    Body JSON:
    {
        "texto": "500 comida enero"
    }
    
    Formato esperado: "[importe] [concepto] [mes]"
    Ejemplos:
    - "500 comida enero"
    - "1000 transporte febrero"
    - "300 ocio marzo"
    """
    try:
        data = request.json
        
        if not data or 'texto' not in data:
            return jsonify({
                'success': False,
                'error': 'Falta el campo "texto". Formato: "500 comida enero"'
            }), 400
        
        texto = data['texto']
        print(f"\n💰 Registrando presupuesto: {texto}")
        
        # Registrar presupuesto
        resultado = registrar_presupuesto(texto)
        
        if resultado['success']:
            print(f"   ✅ {resultado['mensaje']}")
            return jsonify(resultado)
        else:
            print(f"   ❌ Error: {resultado['mensaje']}")
            return jsonify(resultado), 400
    
    except Exception as e:
        print(f"   ❌ Error inesperado: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }), 500

# ============================================================================
# SERVE CRONOGRAMA AND HELPER FUNCTIONS
# ============================================================================

@app.route('/', methods=['GET'])
@app.route('/cronograma', methods=['GET'])
def serve_cronograma():
    """Serve the latest cronograma HTML file with BOE widget"""
    import glob
    
    # Find the latest cronograma HTML file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Try V7 files first, then V7.5
    pattern_v7 = os.path.join(base_dir, 'cronograma_v7_*.html')
    pattern_v7_5 = os.path.join(base_dir, 'cronograma_v7_5_*.html')
    
    html_files = glob.glob(pattern_v7) + glob.glob(pattern_v7_5)
    if not html_files:
        return jsonify({'error': 'No cronograma file found'}), 404
    
    latest_file = max(html_files, key=os.path.getmtime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Inject BOE widget after the title
    boe_widget_path = os.path.join(base_dir, 'templates', 'boe-widget.html')
    if os.path.exists(boe_widget_path):
        with open(boe_widget_path, 'r', encoding='utf-8') as f:
            boe_widget = f.read()
        
        # Insert after the main title/header
        # Look for common patterns in the cronograma HTML
        if '<body' in html_content:
            # Find the end of body tag and insert after it
            body_end = html_content.find('>', html_content.find('<body'))
            if body_end != -1:
                html_content = html_content[:body_end+1] + '\n' + boe_widget + html_content[body_end+1:]
    
    # Add headers to prevent caching
    headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
    
    return html_content, 200, headers

@app.route('/cronograma/manana', methods=['GET'])
def serve_cronograma_manana():
    """Generate and serve tomorrow's cronograma in readonly mode"""
    try:
        print("\n👁️ Generating tomorrow's cronograma (readonly mode)...")
        
        # Run the generator with --tomorrow flag
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env = os.environ.copy()
        result = subprocess.run(
            ['python3.11', 'cronograma_generator_v7_5.py', '--tomorrow'],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        
        if result.returncode == 0:
            # Find the latest generated cronograma
            import glob
            pattern = os.path.join(base_dir, 'cronograma_v7_5_*.html')
            cronogramas = glob.glob(pattern)
            if cronogramas:
                latest = max(cronogramas, key=os.path.getmtime)
                
                with open(latest, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Add readonly indicator and back button
                html_content = html_content.replace(
                    '<button onclick="regenerarCronograma()"',
                    '<a href="/" style="display: inline-block; background: #6b7280; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-right: 10px;">← Volver a Hoy</a><button onclick="regenerarCronograma()" style="display:none"'
                )
                
                # Add readonly notice
                html_content = html_content.replace(
                    '✅ Cronograma V7.5',
                    '👁️ Vista Previa - Mañana (Solo Lectura)'
                )
                
                return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        
        return jsonify({'error': 'Failed to generate tomorrow cronograma'}), 500
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

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
        print("🔄 Using V7.5 generator (Python blocks)...")
        
        # Use V7.5 directly (Python blocks method)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        env = os.environ.copy()
        result = subprocess.run(
            ['python3.11', 'cronograma_generator_v7_5.py'],
            cwd=base_dir,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        
        # Print subprocess output for debugging
        import sys
        if result.stdout:
            print("=== CRONOGRAMA GENERATOR OUTPUT ===", flush=True)
            print(result.stdout, flush=True)
            sys.stdout.flush()
        if result.stderr:
            print("=== CRONOGRAMA GENERATOR ERRORS ===", flush=True)
            print(result.stderr, flush=True)
            sys.stdout.flush()
        
        if result.returncode == 0:
            # Find the latest generated cronograma
            import glob
            pattern = os.path.join(base_dir, 'cronograma_v7_5_*.html')
            cronogramas = glob.glob(pattern)
            if cronogramas:
                latest = max(cronogramas, key=os.path.getmtime)
                return latest
        else:
            print(f"Error generating cronograma: returncode={result.returncode}")
        
        return None
    
    except Exception as e:
        print(f"Error regenerating cronograma: {e}")
        return None

if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("🚀 Starting Cronograma Web Server")
    print("=" * 80)
    print("\nAvailable endpoints:")
    print("  GET  /                        - Serve latest cronograma")
    print("  GET  /cronograma              - Serve latest cronograma")
    print("  GET  /health                  - Health check")
    print("  GET  /boe-subastas            - BOE Subastas Dashboard")
    print("  POST /regenerate              - Regenerate cronograma manually")
    print("  POST /copy-and-regenerate     - Copy event and regenerate")
    print("  POST /ignore-event            - Mark event as ignored")
    print("  POST /complete-task           - Complete task in Todoist and regenerate")
    print("  GET  /new-events              - Get list of new events")
    print("  POST /update-idealista        - Update Idealista data from Node-RED")
    print("  GET  /idealista-data          - Get current Idealista data")
    print("  GET  /firefly-data            - Get Firefly III financial summary")
    print("  POST /registrar-gasto         - Register expense via voice (Siri)")
    print("  POST /registrar-presupuesto   - Register budget via voice (Siri)")
    print("  GET  /categorias              - List available expense categories")
    print("\n" + "=" * 80)
    
    # Run server
    # Use PORT environment variable from Railway, default to 8000 for local development
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)


# ============================================
# CRONOGRAMA DRAG AND DROP ENDPOINTS
# ============================================

@app.route('/cronograma-drag-drop', methods=['GET'])
def cronograma_drag_drop():
    """Render cronograma with drag and drop functionality"""
    try:
        # Read current cronograma HTML
        cronograma_path = '/app/cronograma.html' if os.path.exists('/app/cronograma.html') else 'cronograma.html'
        
        if not os.path.exists(cronograma_path):
            return jsonify({'error': 'Cronograma no encontrado'}), 404
        
        # Parse cronograma data (simplified version)
        # In production, you'd parse the actual cronograma.html
        time_blocks = []
        
        # Generate time blocks from 07:00 to 21:00 in 20-minute intervals
        start_hour = 7
        end_hour = 21
        interval = 20  # minutes
        
        current_minutes = start_hour * 60
        end_minutes = end_hour * 60
        
        while current_minutes < end_minutes:
            hours = current_minutes // 60
            minutes = current_minutes % 60
            time_str = f"{hours:02d}:{minutes:02d}-{(hours + (minutes + interval) // 60):02d}:{(minutes + interval) % 60:02d}"
            
            # Mark fixed blocks
            is_fixed = (hours == 7 and minutes == 0) or (hours == 14 and minutes == 0)
            
            time_blocks.append({
                'time': time_str,
                'is_fixed': is_fixed,
                'task': None  # Will be populated from actual cronograma
            })
            
            current_minutes += interval
        
        # Sample unassigned tasks (in production, get from Todoist)
        unassigned_tasks = [
            {
                'id': 'task-1',
                'emoji': '💪',
                'content': 'Ejercicio de espalda',
                'priority': 'P4',
                'duration': 10,
                'labels': ['fisico', 'hábitos']
            },
            {
                'id': 'task-2',
                'emoji': '📚',
                'content': 'Leer libro de desarrollo personal',
                'priority': 'P3',
                'duration': 20,
                'labels': ['intelectual', 'motivación']
            }
        ]
        
        return render_template('cronograma_drag_drop.html',
                             time_blocks=time_blocks,
                             unassigned_tasks=unassigned_tasks,
                             assigned_count=0,
                             unassigned_count=len(unassigned_tasks),
                             blocks_used=2,
                             total_blocks=len(time_blocks))
    
    except Exception as e:
        print(f"Error rendering drag and drop cronograma: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/cronograma-drag-drop/save', methods=['POST'])
def save_cronograma_changes():
    """Save cronograma changes from drag and drop"""
    try:
        data = request.get_json()
        cronograma = data.get('cronograma', [])
        
        # Save to a JSON file for persistence
        save_path = '/app/cronograma_custom.json' if os.path.exists('/app') else 'cronograma_custom.json'
        
        with open(save_path, 'w') as f:
            json.dump(cronograma, f, indent=2)
        
        print(f"✅ Cronograma personalizado guardado: {len(cronograma)} bloques")
        
        return jsonify({
            'success': True,
            'message': 'Cronograma guardado correctamente',
            'blocks_saved': len(cronograma)
        })
    
    except Exception as e:
        print(f"Error saving cronograma: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

