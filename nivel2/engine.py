import hashlib
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation

def normalized(text):
    return re.sub(r'[^a-z0-9 ]',' ',unicodedata.normalize('NFKD',text or '').encode('ascii','ignore').decode().lower()).strip()

def money(value):
    try:
        d = Decimal(str(value))
        if not d.is_finite() or d < 0 or d != d.quantize(Decimal('.01')):
            raise ValueError('Importe no válido (máximo dos decimales)')
        return d
    except (InvalidOperation, TypeError):
        raise ValueError('Importe no válido')

def signature(tx):
    # Narrow learned rule: description, payee, category, route, currency AND amount.
    fields=[normalized(tx.get(k)) for k in ('description','merchant','financial_category')]
    fields += [str(tx.get(k,'')) for k in ('source_id','destination_id','currency','amount')]
    return hashlib.sha256(json.dumps(fields).encode()).hexdigest()

def eligible(tx):
    # Property expenses can be responsibility, but transfers/income are never consumption.
    return tx['movement_type']=='withdrawal' and (str(tx['source_id']),str(tx['destination_id'])) in {('1','2'),('6','7')}

KEYWORDS = [
 ('C01',r'\b(servo|aeromodelismo|receptor rc|helice|bateria rc)\b'),
 ('C02',r'\b(railway|aplicacion de gastos|firefly)\b'),
 ('C03',r'\bcercedilla\b.*\b(obra|construccion|material|arquitecto)\b'),
 ('R04',r'\b(garaje|plaza)\s+17\b'),('R05',r'\b(garaje|plaza)\s+39\b'),
 ('R02',r'\bplaya samil\s+4\b'),('R03',r'\bplaya samil\s+8\b'),
 ('R01',r'\b(pedro zerolo|vazquez de mella)\b.*\b(fontaneria|ibi|comunidad|reparacion|seguro)\b|\b(fontaneria|ibi|comunidad|reparacion|seguro)\b.*\b(pedro zerolo|vazquez de mella)\b'),
 ('R07',r'\b(dkv|dentista|farmacia|medico)\b'),
 ('E01',r'\b(trekking|senderismo)\b'),('E02',r'\bmicroteatro\b'),
 ('E03',r'\bvolar\b.*\b(rc|radiocontrol)\b'),('E04',r'\b(concierto clasico|musica clasica|mozart|excelentia)\b'),
 ('E05',r'\bpadel\b.*\brivas\b'),('E06',r'\bpadel\b.*\bestudiante\b'),
 ('E07',r'\bclase particular\b.*\bpadel\b'),('E08',r'\bbaqueira\b'),
 ('H01',r'\bleffe\b'),('H02',r'\bmaroma\b'),
]

def propose(tx, units, rule=None):
    if not eligible(tx):
        return {'status':'excluded','confidence':0,'reason':'Ingreso, transferencia o ruta fuera del ámbito personal/patrimonial configurado','allocations':[]}
    ids={u['id']:u for u in units}
    if rule and rule['unit_id'] in ids:
        return {'status':'proposed','confidence':.95,'reason':'Regla aprendida de una corrección confirmada; requiere confirmación','allocations':[{'unit_id':rule['unit_id'],'amount':str(tx['amount']),'obligation':rule['obligation']}]}
    text=normalized(tx['description']+' '+(tx.get('merchant') or ''))
    matches=[uid for uid,pattern in KEYWORDS if uid in ids and re.search(pattern,text)]
    if len(matches)!=1:
        return {'status':'pending','confidence':0,'reason':'Sin evidencia suficiente' if not matches else 'Varias unidades posibles; confirma el reparto','allocations':[]}
    uid=matches[0]; unit=ids[uid]
    confidence=.65
    if tx.get('currency')=='EUR' and unit.get('standard_cost') is not None and money(tx['amount'])==money(unit['standard_cost']): confidence+=.05
    if normalized(tx.get('financial_category')) in ('salud','ocio','casa'): confidence+=.02
    # UGE satisfaction/time are references, never transaction observations.
    return {'status':'proposed','confidence':confidence,'reason':'Coincidencia orientativa de descripción/destinatario; no demuestra actividad ni compañía','allocations':[{'unit_id':uid,'amount':str(tx['amount']),'obligation':'desconocido'}]}

def validate_allocations(rows,total,unit_ids):
    if not rows or len(rows)>50: raise ValueError('Añade entre 1 y 50 imputaciones')
    seen=set(); summed=Decimal('0')
    for row in rows:
        if row['unit_id'] not in unit_ids or row['unit_id'] in seen: raise ValueError('Unidad inválida o repetida')
        seen.add(row['unit_id'])
        if row['obligation'] not in ('obligado','discrecional','desconocido'): raise ValueError('Naturaleza inválida')
        value=money(row['amount'])
        if value<=0: raise ValueError('La imputación debe ser positiva')
        summed+=value
    if summed!=money(total): raise ValueError('El reparto debe sumar exactamente el importe del movimiento')
