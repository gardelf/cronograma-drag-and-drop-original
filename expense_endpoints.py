# Expense API endpoints to add to web_server.py
import re
import requests
import os
from datetime import datetime

# Categorías conocidas para gastos (basadas en Firefly III)
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
    openai_api_key = os.getenv('OPENAI_API_KEY', '')
    
    if not openai_api_key:
        return None
    
    try:
        categorias_str = ', '.join([cat.capitalize() for cat in CATEGORIAS_CONOCIDAS.keys()])
        
        prompt = f"""Categoriza el siguiente gasto en UNA de estas categorías: {categorias_str}

Gasto: {descripcion}

Responde SOLO con el nombre de la categoría, nada más."""

        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {openai_api_key}',
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
        from config import get_config
        config = get_config()
        
        firefly_url = config.get('FIREFLY_URL', '')
        firefly_token = config.get('FIREFLY_TOKEN', '')
        
        if not firefly_url or not firefly_token:
            return False, 'Firefly III no configurado'
        
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
            f'{firefly_url}/api/v1/transactions',
            headers={
                'Authorization': f'Bearer {firefly_token}',
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


# ========== FUNCIONES PARA PRESUPUESTOS ==========

MESES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}

def extraer_presupuesto_datos(texto):
    """
    Extrae importe, concepto y mes del texto
    Ejemplos: "500 comida enero", "1000 transporte febrero", "300 ocio marzo"
    """
    texto = texto.strip().lower()
    
    # Buscar patrón: número + concepto + mes
    # Ejemplo: "500 comida enero"
    match = re.match(r'(\d+(?:[.,]\d+)?)\s+(.+?)\s+(' + '|'.join(MESES.keys()) + r')', texto)
    
    if match:
        monto_str = match.group(1).replace(',', '.')
        concepto = match.group(2).strip().capitalize()
        mes_nombre = match.group(3)
        mes_numero = MESES[mes_nombre]
        
        return float(monto_str), concepto, mes_numero
    
    return None, None, None


def obtener_fechas_mes(mes_numero, año=None):
    """
    Devuelve las fechas de inicio y fin de un mes
    """
    if año is None:
        año = datetime.now().year
    
    # Primer día del mes
    start = f"{año}-{mes_numero:02d}-01"
    
    # Último día del mes
    if mes_numero == 12:
        end = f"{año}-12-31"
    else:
        # Usar el día anterior al primer día del mes siguiente
        from calendar import monthrange
        ultimo_dia = monthrange(año, mes_numero)[1]
        end = f"{año}-{mes_numero:02d}-{ultimo_dia}"
    
    return start, end


def buscar_o_crear_budget(concepto):
    """
    Busca un budget por nombre, si no existe lo crea
    Devuelve el ID del budget
    """
    try:
        from config import get_config
        config = get_config()
        
        firefly_url = config.get('FIREFLY_URL', '')
        firefly_token = config.get('FIREFLY_TOKEN', '')
        
        if not firefly_url or not firefly_token:
            return None, 'Firefly III no configurado'
        
        headers = {
            'Authorization': f'Bearer {firefly_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # 1. Buscar si ya existe el budget
        response = requests.get(
            f'{firefly_url}/api/v1/budgets',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            budgets = response.json().get('data', [])
            for budget in budgets:
                if budget['attributes']['name'].lower() == concepto.lower():
                    return budget['id'], None
        
        # 2. Si no existe, crear el budget
        payload = {
            "name": concepto,
            "active": True
        }
        
        response = requests.post(
            f'{firefly_url}/api/v1/budgets',
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            budget_id = response.json()['data']['id']
            return budget_id, None
        else:
            return None, f"Error al crear budget: {response.status_code} - {response.text}"
    
    except Exception as e:
        return None, str(e)


def crear_budget_limit(budget_id, monto, start, end):
    """
    Crea un budget limit (límite de presupuesto) para un budget específico
    """
    try:
        from config import get_config
        config = get_config()
        
        firefly_url = config.get('FIREFLY_URL', '')
        firefly_token = config.get('FIREFLY_TOKEN', '')
        
        if not firefly_url or not firefly_token:
            return False, 'Firefly III no configurado'
        
        payload = {
            "currency_code": "EUR",
            "start": start,
            "end": end,
            "amount": str(monto)
        }
        
        response = requests.post(
            f'{firefly_url}/api/v1/budgets/{budget_id}/limits',
            headers={
                'Authorization': f'Bearer {firefly_token}',
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


def registrar_presupuesto(texto):
    """
    Función principal para registrar un presupuesto desde texto
    Ejemplo: "500 comida enero"
    """
    # 1. Extraer datos del texto
    monto, concepto, mes_numero = extraer_presupuesto_datos(texto)
    
    if not monto or not concepto or not mes_numero:
        return {
            'success': False,
            'mensaje': 'No se pudo interpretar el presupuesto. Formato: "500 comida enero"'
        }
    
    # 2. Obtener fechas del mes
    start, end = obtener_fechas_mes(mes_numero)
    
    # 3. Buscar o crear el budget
    budget_id, error = buscar_o_crear_budget(concepto)
    
    if error:
        return {
            'success': False,
            'mensaje': f'Error al buscar/crear budget: {error}'
        }
    
    # 4. Crear el budget limit
    success, result = crear_budget_limit(budget_id, monto, start, end)
    
    if success:
        mes_nombre = [k for k, v in MESES.items() if v == mes_numero][0]
        return {
            'success': True,
            'mensaje': f'Presupuesto registrado: {monto}€ para {concepto} en {mes_nombre.capitalize()}',
            'datos': {
                'monto': monto,
                'concepto': concepto,
                'mes': mes_nombre.capitalize(),
                'periodo': f'{start} a {end}'
            }
        }
    else:
        return {
            'success': False,
            'mensaje': f'Error al crear presupuesto: {result}'
        }
