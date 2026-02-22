"""
Utilidades para categorización y registro de gastos
"""
import re
import requests
from datetime import datetime
import os


# Mapa de números en texto a dígitos
NUMEROS_TEXTO = {
    'cero': 0, 'uno': 1, 'dos': 2, 'tres': 3, 'cuatro': 4,
    'cinco': 5, 'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9,
    'diez': 10, 'once': 11, 'doce': 12, 'trece': 13, 'catorce': 14,
    'quince': 15, 'dieciséis': 16, 'diecisiete': 17, 'dieciocho': 18,
    'diecinueve': 19, 'veinte': 20, 'treinta': 30, 'cuarenta': 40,
    'cincuenta': 50, 'sesenta': 60, 'setenta': 70, 'ochenta': 80,
    'noventa': 90, 'cien': 100, 'ciento': 100, 'doscientos': 200,
    'trescientos': 300, 'cuatrocientos': 400, 'quinientos': 500,
    'seiscientos': 600, 'setecientos': 700, 'ochocientos': 800,
    'novecientos': 900, 'mil': 1000
}

# Categorías conocidas para gastos (basadas en Firefly III)
CATEGORIAS_CONOCIDAS = {
    'comida': ['mercadona', 'lidl', 'carrefour', 'supermercado', 'restaurante', 'comida', 'cena', 'almuerzo', 'desayuno', 'bar', 'cafetería'],
    'coche': ['gasolina', 'combustible', 'repsol', 'cepsa', 'parking', 'aparcamiento', 'taller', 'mecánico', 'neumáticos'],
    'casa': ['alquiler', 'piso', 'luz', 'agua', 'gas', 'internet', 'móvil', 'climatización'],
    'ocio': ['cine', 'teatro', 'concierto', 'bar', 'pub', 'discoteca', 'pádel', 'gimnasio', 'batería', 'clases'],
    'salud': ['farmacia', 'médico', 'dentista', 'hospital', 'seguro'],
    'transporte': ['taxi', 'uber', 'metro', 'bus', 'tren', 'avión', 'billete'],
    'viajes': ['viaje', 'viajes', 'hotel', 'hospedaje', 'vuelo', 'baqueira', 'barcelona', 'andorra', 'sevilla', 'bilbao', 'valencia', 'malaga', 'palma'],
    'ropa': ['zara', 'hm', 'ropa', 'zapatos', 'zapatería', 'tienda'],
    'formación': ['curso', 'libro', 'academia', 'tradingview', 'tradeando'],
    'inversión': ['acciones', 'bolsa', 'etf', 'fondo'],
    'extraordinario': ['regalo', 'gafas', 'extra', 'especial', 'extraordinario'],
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

Reglas especiales para Viajes:
- Si es un gasto para viaje o desplazamiento a mas de 30 km desde Madrid (hotel, vuelo, tren, gasolina para viaje a otra ciudad, etc.), usa 'Viajes'
- Si es transporte local en Madrid (taxi, metro, bus), usa 'Transporte'
- Si es gasolina para el coche local, usa 'Coche'

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


def registrar_en_firefly(monto, descripcion, categoria, fecha=None, tags=None):
    """Registra el gasto en Firefly III con soporte para tags"""
    try:
        from config import get_config
        config = get_config()
        
        firefly_url = config.get('FIREFLY_URL', '')
        firefly_token = config.get('FIREFLY_TOKEN', '')
        
        if not firefly_url or not firefly_token:
            return False, 'Firefly III no configurado'
        
        # Usar fecha proporcionada o fecha actual
        if fecha is None:
            fecha = datetime.now().strftime('%Y-%m-%d')
        
        # Construir transaccion
        transaction = {
            "type": "withdrawal",
            "date": fecha,
            "amount": str(monto),
            "description": descripcion,
            "source_name": "Fernando Garrido",
            "destination_name": "Cash",
            "category_name": categoria
        }
        
        # Agregar tags si existen
        if tags and len(tags) > 0:
            transaction["tags"] = tags
        
        payload = {
            "error_if_duplicate_hash": False,
            "apply_rules": True,
            "fire_webhooks": True,
            "transactions": [transaction]
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


def extraer_tags_del_texto(texto):
    """Extrae tags del texto (principalmente 'extraordinario')"""
    import re
    
    texto_lower = texto.lower()
    tags = []
    texto_limpio = texto
    
    # Detectar la palabra "extraordinario"
    if 'extraordinario' in texto_lower:
        tags.append('Extraordinario')
        # Remover la palabra del texto
        texto_limpio = re.sub(r'\bextraordinario\b', '', texto, flags=re.IGNORECASE).strip()
    
    return tags, texto_limpio


def extraer_fecha_del_texto(texto):
    """Extrae fecha del texto si está presente"""
    from datetime import datetime, timedelta
    import re
    
    texto_lower = texto.lower()
    hoy = datetime.now()
    
    # Detectar "ayer"
    if 'ayer' in texto_lower:
        fecha = hoy - timedelta(days=1)
        texto_limpio = re.sub(r'\bayer\b', '', texto, flags=re.IGNORECASE).strip()
        return fecha.strftime('%Y-%m-%d'), texto_limpio
    
    # Detectar "anteayer"
    if 'anteayer' in texto_lower or 'ante ayer' in texto_lower:
        fecha = hoy - timedelta(days=2)
        texto_limpio = re.sub(r'\b(anteayer|ante ayer)\b', '', texto, flags=re.IGNORECASE).strip()
        return fecha.strftime('%Y-%m-%d'), texto_limpio
    
    # Detectar formato "10 diciembre", "15 enero", "1 de enero de 2026", etc.
    meses = {
        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
    }
    
    for mes_nombre, mes_num in meses.items():
        # Buscar patrón "día de mes de año" (ej: "1 de enero de 2026")
        pattern = rf'\b(\d{{1,2}})\s+de\s+{mes_nombre}\s+de\s+(\d{{4}})\b'
        match = re.search(pattern, texto_lower)
        if match:
            dia = int(match.group(1))
            año = int(match.group(2))
            fecha = datetime(año, mes_num, dia)
            texto_limpio = re.sub(pattern, '', texto, flags=re.IGNORECASE).strip()
            return fecha.strftime('%Y-%m-%d'), texto_limpio
        
        # Buscar patrón "día mes año" (ej: "10 diciembre 2026")
        pattern = rf'\b(\d{{1,2}})\s+{mes_nombre}\s+(\d{{4}})\b'
        match = re.search(pattern, texto_lower)
        if match:
            dia = int(match.group(1))
            año = int(match.group(2))
            fecha = datetime(año, mes_num, dia)
            texto_limpio = re.sub(pattern, '', texto, flags=re.IGNORECASE).strip()
            return fecha.strftime('%Y-%m-%d'), texto_limpio
        
        # Buscar patrón "día mes" (ej: "10 diciembre")
        pattern = rf'\b(\d{{1,2}})\s+{mes_nombre}\b'
        match = re.search(pattern, texto_lower)
        if match:
            dia = int(match.group(1))
            año = hoy.year
            # Si el mes ya pasó este año, asumir año siguiente
            if mes_num < hoy.month or (mes_num == hoy.month and dia < hoy.day):
                año = hoy.year + 1
            fecha = datetime(año, mes_num, dia)
            texto_limpio = re.sub(pattern, '', texto, flags=re.IGNORECASE).strip()
            return fecha.strftime('%Y-%m-%d'), texto_limpio
    
    # Detectar formato "DD/MM/YYYY" o "DD-MM-YYYY"
    match = re.search(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', texto)
    if match:
        dia, mes, año = match.groups()
        try:
            fecha = datetime(int(año), int(mes), int(dia))
            texto_limpio = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b', '', texto).strip()
            return fecha.strftime('%Y-%m-%d'), texto_limpio
        except:
            pass
    
    # Detectar solo el mes (sin día) - retorna el 1 del mes
    for mes_nombre, mes_num in meses.items():
        # Buscar patrón solo mes (ej: "febrero", "marzo")
        pattern = rf'^{mes_nombre}$|\b{mes_nombre}\b(?!\s+de|\s+\d)'
        match = re.search(pattern, texto_lower)
        if match:
            dia = 1  # Primer día del mes
            año = hoy.year
            # Si el mes ya pasó este año, asumir año siguiente
            if mes_num < hoy.month:
                año = hoy.year + 1
            fecha = datetime(año, mes_num, dia)
            # Remover el mes del texto
            texto_limpio = re.sub(rf'\b{mes_nombre}\b', '', texto, flags=re.IGNORECASE).strip()
            return fecha.strftime('%Y-%m-%d'), texto_limpio
    
    # Si no se detecta fecha, devolver None y texto original
    return None, texto


def extraer_categoria_manual(texto):
    """Extrae categoría manual si está presente en el texto"""
    import re
    
    # Buscar patrón "categoría X" o "categoria X"
    match = re.search(r'categor[ií]a\s+(\w+)', texto, flags=re.IGNORECASE)
    if match:
        categoria = match.group(1).capitalize()
        texto_limpio = re.sub(r'categor[ií]a\s+\w+', '', texto, flags=re.IGNORECASE).strip()
        return categoria, texto_limpio
    
    return None, texto


def extraer_datos_con_ia(texto):
    """Usa ChatGPT para extraer monto, descripción, fecha, categoría y tags del texto"""
    # Primero extraer tags (extraordinario) del texto
    tags, texto_sin_tags = extraer_tags_del_texto(texto)
    openai_api_key = os.getenv('OPENAI_API_KEY', '')
    
    if not openai_api_key:
        # Si no hay API key, usar método tradicional
        return extraer_monto_descripcion_regex(texto)
    
    try:
        from datetime import datetime
        hoy = datetime.now().strftime('%Y-%m-%d')
        
        categorias_str = ', '.join([cat.capitalize() for cat in CATEGORIAS_CONOCIDAS.keys()])
        
        prompt = f"""Extrae la siguiente información del texto de gasto:

Texto: "{texto}"

Fecha de hoy: {hoy}

Extrae:
1. Monto (número decimal). Si el monto está escrito en texto ("uno", "dos", "tres", etc.), convértelo a número (1, 2, 3, etc.)
2. Descripción (texto del gasto, sin fecha ni categoría)
3. Fecha (formato YYYY-MM-DD, si no se menciona usa {hoy})
4. Categoría (si se menciona explícitamente, sino devuelve null). Categorías válidas: {categorias_str}

Responde SOLO con JSON:
{{
  "monto": 100.0,
  "descripcion": "gafas de sol",
  "fecha": "2026-01-01",
  "categoria": "Extraordinario"
}}

Ejemplos:
- "uno euro comida" → {{"monto": 1.0, "descripcion": "comida", "fecha": "{hoy}", "categoria": null}}
- "dos euros cincuenta café" → {{"monto": 2.50, "descripcion": "café", "fecha": "{hoy}", "categoria": null}}

Si no se menciona fecha, usa {hoy}.
Si no se menciona categoría, usa null."""

        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {openai_api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': [
                    {'role': 'system', 'content': 'Eres un asistente que extrae datos de gastos. Responde solo con JSON válido.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.1,
                'max_tokens': 150
            },
            timeout=10
        )
        
        if response.status_code == 200:
            import json
            contenido = response.json()['choices'][0]['message']['content'].strip()
            # Limpiar posibles marcadores de código
            contenido = contenido.replace('```json', '').replace('```', '').strip()
            datos = json.loads(contenido)
            
            monto = float(datos.get('monto', 0))
            descripcion = datos.get('descripcion', '')
            fecha = datos.get('fecha')
            categoria = datos.get('categoria')
            
            return monto, descripcion, fecha, categoria, tags
        
    except Exception as e:
        print(f"Error en IA para extracción: {e}")
    
    # Si falla IA, usar método tradicional
    return extraer_monto_descripcion_regex(texto)


def extraer_monto_descripcion_regex(texto):
    """Extrae monto, descripción, fecha, categoría y tags del texto de voz usando regex"""
    # Primero extraer tags si existen (ej: extraordinario)
    tags, texto = extraer_tags_del_texto(texto)
    
    # Luego extraer categoría manual si existe
    categoria_manual, texto = extraer_categoria_manual(texto)
    
    # Luego extraer fecha si existe
    fecha, texto = extraer_fecha_del_texto(texto)
    
    # Buscar patrón: número (con o sin decimales) seguido de texto
    # Ejemplos: "25.50 Mercadona", "60 gasolina", "150 restaurante con Cris"
    
    # Intentar con decimales primero
    match = re.match(r'(\d+[.,]\d+)\s+(.+)', texto.strip())
    if match:
        monto_str = match.group(1).replace(',', '.')
        descripcion = match.group(2).strip()
        return float(monto_str), descripcion, fecha, categoria_manual, tags
    
    # Intentar sin decimales
    match = re.match(r'(\d+)\s+(.+)', texto.strip())
    if match:
        monto = float(match.group(1))
        descripcion = match.group(2).strip()
        return monto, descripcion, fecha, categoria_manual, tags
    
    return None, None, None, None, []


def extraer_monto_descripcion(texto):
    """Extrae monto, descripción, fecha y categoría del texto (usa IA si está disponible)"""
    return extraer_datos_con_ia(texto)


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
