"""
Endpoint adicional para generar cronograma manualmente
Añadir a web_server.py
"""

@app.route('/generate-cronograma', methods=['GET', 'POST'])
def generate_cronograma():
    """
    Endpoint para generar cronograma manualmente
    Útil para cron jobs externos
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
