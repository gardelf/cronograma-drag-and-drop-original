#!/usr/bin/env python3
"""
API para registro de gastos por voz con categorización automática por IA
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from datetime import datetime
import re

app = Flask(__name__)
CORS(app)

# Configuración
FIREFLY_URL = os.getenv('FIREFLY_URL', 'https://firefly-core-production-f02a.up.railway.app')
FIREFLY_TOKEN = os.getenv('FIREFLY_TOKEN', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Categorías conocidas (basadas en tus datos de Firefly III)
CATEGORIAS_CONOCIDAS = {
    'comida': ['mercadona', 'lidl', 'carrefour', 'supermercado', 'restaurante', 'comida', 'cena', 'almuerzo', 'desayuno', 'bar', 'cafetería'],
    'coche': ['gasolina', 'combustible', 'repsol', 'cepsa', 'parking', 'aparcamiento', 'taller', 'mecánico', 'neumáticos'],
    'casa': ['alquiler', 'piso', 'luz', 'agua', 'gas', 'internet', 'móvil', 'climatización'],
    'ocio': ['cine', 'teatro', 'concierto', 'bar', 'pub', 'discoteca', 'pádel', 'gimnasio', 'batería', 'clases'],
    'salud': ['farmacia', 'médico', 'dentista', 'hospital', 'seguro'],
    'transporte': ['taxi', 'uber', 'metro', 'bus', 'tren', 'avión', 'billete'],
    'ropa': ['zara', 'hm', 'ropa', 'zapatos', 'zapatería', 'tienda'],
    'formación': ['curso', 'libro', 'academia', 'tradingview', 'tradeando'],
    'inversión': ['acciones', 'bolsa', 'etf', 'fondo'],
}


def categorizar_con_reglas(descripcion):
    """Categoriza usando reglas simples basadas en palabras clave"""
    descripcion_lower = descripcion.lower()
    
    for categoria, palabras_clave in CATEGORIAS_CONOCIDAS.items():
        for palabra in palabras_clave:
            if palabra in descripcion_lower:
                return categoria.capitalize()
    
    return None


def categorizar_con_ia(descripcion):
    """Categoriza usando OpenAI GPT"""
    if not OPENAI_API_KEY:
        return None
    
    try:
        categorias_str = ', '.join([cat.capitalize() for cat in CATEGORIAS_CONOCIDAS.keys()])
        
        prompt = f"""Categoriza el siguiente gasto en UNA de estas categorías: {categorias_str}

Gasto: {descripcion}

Responde SOLO con el nombre de la categoría, nada más."""

        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [
                    {'role': 'system', 'content': 'Eres un asistente que categoriza gastos. Responde solo con el nombre de la categoría.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 20
            },
            timeout=10
        )
        
        if response.status_code == 200:
            categoria = response.json()['choices'][0]['message']['content'].strip()
            return categoria
        
    except Exception as e:
        print(f"Error en IA: {e}")
    
    return None


def categorizar_gasto(descripcion):
    """Categoriza un gasto usando reglas primero, luego IA si es necesario"""
    # Intentar con reglas simples primero
    categoria = categorizar_con_reglas(descripcion)
    
    if categoria:
        return categoria, 'reglas'
    
    # Si no funciona, usar IA
    categoria = categorizar_con_ia(descripcion)
    
    if categoria:
        return categoria, 'ia'
    
    # Si nada funciona, usar categoría por defecto
    return 'Otros', 'default'


def registrar_en_firefly(monto, descripcion, categoria):
    """Registra el gasto en Firefly III"""
    try:
        fecha = datetime.now().strftime('%Y-%m-%d')
        
        payload = {
            "error_if_duplicate_hash": False,
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [{
                "type": "withdrawal",
                "date": fecha,
                "amount": str(monto),
                "description": descripcion,
                "source_name": "Fernando Garrido",
                "destination_name": "Cash",
                "category_name": categoria
            }]
        }
        
        response = requests.post(
            f'{FIREFLY_URL}/api/v1/transactions',
            headers={
                'Authorization': f'Bearer {FIREFLY_TOKEN}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return True, response.json()
        else:
            return False, f"Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return False, str(e)


def extraer_monto_descripcion(texto):
    """Extrae monto y descripción del texto de voz"""
    # Buscar patrón: número (con o sin decimales) seguido de texto
    # Ejemplos: "25.50 Mercadona", "60 gasolina", "150 restaurante con Cris"
    
    # Intentar con decimales primero
    match = re.match(r'(\d+[.,]\d+)\s+(.+)', texto.strip())
    if match:
        monto_str = match.group(1).replace(',', '.')
        descripcion = match.group(2)
        return float(monto_str), descripcion
    
    # Intentar sin decimales
    match = re.match(r'(\d+)\s+(.+)', texto.strip())
    if match:
        monto = float(match.group(1))
        descripcion = match.group(2)
        return monto, descripcion
    
    return None, None


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'expense-api'})


@app.route('/registrar-gasto', methods=['POST'])
def registrar_gasto():
    """
    Endpoint para registrar un gasto
    
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
        
        # Opción 1: Texto completo (desde Siri)
        if 'texto' in data:
            texto = data['texto']
            monto, descripcion = extraer_monto_descripcion(texto)
            
            if monto is None or descripcion is None:
                return jsonify({
                    'success': False,
                    'error': 'No se pudo extraer monto y descripción del texto. Formato esperado: "25.50 Mercadona"'
                }), 400
        
        # Opción 2: Monto y descripción separados
        elif 'monto' in data and 'descripcion' in data:
            monto = float(data['monto'])
            descripcion = data['descripcion']
        
        else:
            return jsonify({
                'success': False,
                'error': 'Faltan datos. Envía "texto" o "monto" + "descripcion"'
            }), 400
        
        # Categorizar
        categoria, metodo = categorizar_gasto(descripcion)
        
        # Registrar en Firefly III
        exito, resultado = registrar_en_firefly(monto, descripcion, categoria)
        
        if exito:
            return jsonify({
                'success': True,
                'monto': monto,
                'descripcion': descripcion,
                'categoria': categoria,
                'metodo_categorizacion': metodo,
                'mensaje': f"Registrado: {monto} euros en {categoria}",
                'firefly_response': resultado
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Error al registrar en Firefly III: {resultado}'
            }), 500
            
    except Exception as e:
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


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
