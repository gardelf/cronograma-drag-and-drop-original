import hmac
import os
import uuid
from datetime import date
from decimal import Decimal
from urllib.parse import urlsplit
from flask import Blueprint, jsonify, request, render_template
from werkzeug.exceptions import HTTPException
from psycopg2.extras import Json
from .db import connect
from .engine import money, signature, validate_allocations

bp=Blueprint('nivel2',__name__,url_prefix='/nivel2',template_folder='templates')

@bp.before_request
def protect():
    expected=os.environ.get('NIVEL2_ACCESS_TOKEN','')
    auth=request.authorization
    if not expected: return jsonify(error='Nivel 2 pendiente de configurar acceso'),503
    if not auth or auth.username!='nivel2' or not hmac.compare_digest(auth.password or '',expected):
        return ('Acceso al Nivel 2',401,{'WWW-Authenticate':'Basic realm="Nivel 2", charset="UTF-8"'})
    if request.method not in ('GET','HEAD','OPTIONS'):
        origin=request.headers.get('Origin')
        if request.headers.get('X-Nivel2-Request')!='1' or not request.is_json or (origin and urlsplit(origin).netloc!=request.host):
            return jsonify(error='Solicitud no permitida'),403

@bp.after_request
def private(response):
    response.headers['Cache-Control']='no-store'
    return response

@bp.errorhandler(ValueError)
def invalid(exc): return jsonify(error=str(exc)),400

@bp.errorhandler(Exception)
def failed(exc):
    if isinstance(exc, HTTPException): return exc
    print('Nivel2 request error:',type(exc).__name__,flush=True)
    return jsonify(error='Nivel 2 no disponible; revisa configuración, migraciones y conexión PostgreSQL'),503

@bp.get('')
@bp.get('/')
def index(): return render_template('nivel2.html')

@bp.get('/api/matrix')
def matrix():
    with connect() as c,c.cursor() as q:
        q.execute('SELECT * FROM n2_values ORDER BY code'); values=q.fetchall()
        q.execute('SELECT * FROM n2_units ORDER BY id'); units=q.fetchall()
        q.execute('SELECT * FROM n2_components ORDER BY id'); components=q.fetchall()
    for unit in units: unit['components']=[x for x in components if x['unit_id']==unit['id']]
    return jsonify(values=values,units=units)

def optional_number(v,maximum=None):
    if v is None or v=='': return None
    result=money(v)
    if maximum is not None and result>maximum: raise ValueError('Valor fuera de rango')
    return result

@bp.post('/api/units')
def save_unit():
    data=request.get_json(); uid=data.get('id') or 'U-'+str(uuid.uuid4())
    name=str(data.get('name','')).strip()
    if not name or len(name)>250: raise ValueError('Nombre obligatorio (máximo 250 caracteres)')
    kind=data.get('cost_kind')
    if kind not in ('fixed','variable','unknown'): raise ValueError('Tipo de coste inválido')
    cost=optional_number(data.get('standard_cost'))
    if kind=='unknown': cost=None
    if kind=='fixed' and cost is None: raise ValueError('Indica el coste fijo')
    satisfaction=optional_number(data.get('satisfaction'),10); hours=optional_number(data.get('hours'))
    components=data.get('components',[])
    if len(components)>50: raise ValueError('Máximo 50 componentes')
    for component in components:
        if not str(component.get('name','')).strip(): raise ValueError('Nombre de componente obligatorio')
        component['cost']=optional_number(component.get('cost'))
    if components and kind=='fixed':
        if any(x['cost'] is None for x in components) or sum(x['cost'] for x in components)!=cost:
            raise ValueError('Los componentes deben sumar la UGE fija; usa variable/desconocido si faltan importes')
    with connect() as c,c.cursor() as q:
        q.execute('SELECT * FROM n2_values WHERE code=%s',(data.get('value_code'),)); value=q.fetchone()
        if not value: raise ValueError('Valor personal inválido')
        if not value['experiential'] and (satisfaction is not None or hours is not None): raise ValueError('Esta categoría no registra satisfacción ni tiempo')
        q.execute('SELECT * FROM n2_units WHERE id=%s FOR UPDATE',(uid,)); old=q.fetchone()
        if old and old['version']!=data.get('version'): return jsonify(error='La unidad cambió; vuelve a cargarla'),409
        if old and old['value_code']!=data['value_code']: raise ValueError('La categoría de una unidad es permanente; crea otra unidad')
        q.execute('''INSERT INTO n2_units(id,value_code,name,cost_kind,standard_cost,satisfaction,hours,time_note) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
          ON CONFLICT(id) DO UPDATE SET name=EXCLUDED.name,cost_kind=EXCLUDED.cost_kind,standard_cost=EXCLUDED.standard_cost,satisfaction=EXCLUDED.satisfaction,hours=EXCLUDED.hours,time_note=EXCLUDED.time_note,version=n2_units.version+1''',
          (uid,data['value_code'],name,kind,cost,satisfaction,hours,str(data.get('time_note',''))[:2000]))
        q.execute('DELETE FROM n2_components WHERE unit_id=%s',(uid,))
        for x in components: q.execute('INSERT INTO n2_components(unit_id,name,cost) VALUES (%s,%s,%s)',(uid,str(x['name'])[:250],x['cost']))
    return jsonify(id=uid)

def period():
    start=date.fromisoformat(request.args.get('start',date.today().replace(day=1).isoformat()))
    end=date.fromisoformat(request.args.get('end',date.today().isoformat()))
    if end<start: raise ValueError('Periodo inválido')
    return start,end

@bp.get('/api/transactions')
def transactions():
    start,end=period(); page=max(1,int(request.args.get('page',1))); status=request.args.get('status','all')
    clause=" AND t.status IN ('pending','proposed','review') AND NOT t.deleted" if status=='pending' else ''
    with connect() as c,c.cursor() as q:
        q.execute('SELECT count(*) AS count FROM n2_transactions t WHERE occurred_on BETWEEN %s AND %s'+clause,(start,end)); count=q.fetchone()['count']
        q.execute('SELECT t.* FROM n2_transactions t WHERE occurred_on BETWEEN %s AND %s'+clause+' ORDER BY occurred_on DESC,id DESC LIMIT 100 OFFSET %s',(start,end,(page-1)*100)); rows=q.fetchall()
        for t in rows:
            t.pop('raw');t['occurred_on']=t['occurred_on'].isoformat()
            q.execute('SELECT a.*,u.name,u.value_code FROM n2_allocations a JOIN n2_units u ON u.id=a.unit_id WHERE transaction_id=%s',(t['id'],));t['allocations']=q.fetchall()
    return jsonify(items=rows,total=count,page=page)

@bp.post('/api/transactions/<int:tid>/confirm')
def confirm(tid):
    data=request.get_json(); rows=data.get('allocations',[])
    with connect() as c,c.cursor() as q:
        q.execute('SELECT * FROM n2_transactions WHERE id=%s FOR UPDATE',(tid,)); tx=q.fetchone()
        if not tx: return jsonify(error='Movimiento inexistente'),404
        if data.get('version')!=tx['version']: return jsonify(error='El movimiento cambió; vuelve a cargarlo'),409
        if tx['deleted'] or not tx['eligible']: raise ValueError('Este movimiento no es un gasto elegible')
        q.execute('SELECT id FROM n2_units'); ids={r['id'] for r in q.fetchall()}
        exclude=data.get('exclude') is True
        if not exclude: validate_allocations(rows,tx['amount'],ids)
        else: rows=[]
        q.execute('SELECT unit_id,amount,obligation FROM n2_allocations WHERE transaction_id=%s',(tid,)); previous=q.fetchall()
        before={'status':tx['status'],'allocations':[{**r,'amount':str(r['amount'])} for r in previous]}
        q.execute('DELETE FROM n2_allocations WHERE transaction_id=%s',(tid,))
        for row in rows: q.execute('INSERT INTO n2_allocations(transaction_id,unit_id,amount,obligation) VALUES (%s,%s,%s,%s)',(tid,row['unit_id'],money(row['amount']),row['obligation']))
        new_status='excluded' if exclude else 'confirmed'
        q.execute('UPDATE n2_transactions SET status=%s,confidence=1,reason=%s,version=version+1 WHERE id=%s',(new_status,'Confirmado por el usuario',tid))
        q.execute('INSERT INTO n2_corrections(transaction_id,action,before_data,after_data) VALUES (%s,%s,%s,%s)',(tid,'user_correction',Json(before),Json({'status':new_status,'allocations':rows})))
        if len(rows)==1:
            row=rows[0]
            q.execute('''INSERT INTO n2_rules(signature,unit_id,obligation) VALUES (%s,%s,%s) ON CONFLICT(signature) DO UPDATE SET unit_id=EXCLUDED.unit_id,obligation=EXCLUDED.obligation,confirmations=n2_rules.confirmations+1,updated_at=now()''',(signature(tx),row['unit_id'],row['obligation']))
        else: q.execute('DELETE FROM n2_rules WHERE signature=%s',(signature(tx),))
    return jsonify(status=new_status)

@bp.get('/api/summary')
def summary():
    start,end=period()
    with connect() as c,c.cursor() as q:
        q.execute('''SELECT u.value_code,u.id AS unit_id,u.name,t.currency,a.obligation,sum(a.amount) AS amount FROM n2_allocations a
          JOIN n2_transactions t ON t.id=a.transaction_id JOIN n2_units u ON u.id=a.unit_id
          WHERE t.status='confirmed' AND t.deleted=false AND t.eligible AND t.occurred_on BETWEEN %s AND %s
          GROUP BY u.value_code,u.id,u.name,t.currency,a.obligation ORDER BY u.value_code,u.name''',(start,end)); rows=q.fetchall()
        q.execute("SELECT status,currency,count(*) AS count,sum(amount) AS amount FROM n2_transactions WHERE occurred_on BETWEEN %s AND %s AND deleted=false GROUP BY status,currency",(start,end)); coverage=q.fetchall()
    return jsonify(items=rows,coverage=coverage)

@bp.get('/api/sync-status')
def sync_status():
    with connect() as c,c.cursor() as q:
        q.execute('SELECT * FROM n2_sync_runs ORDER BY id DESC LIMIT 10'); rows=q.fetchall()
    return jsonify(runs=rows)

def register(app):
    if 'nivel2' in app.blueprints: return
    app.register_blueprint(bp)
    # This response hook affects ONLY Level 2, even if the base app enables CORS.
    def isolate_n2(response):
        if request.path == '/sandbox' and response.status_code == 200 and response.mimetype == 'text/html':
            html = response.get_data(as_text=True)
            link = '<a href="/nivel2" style="display:block;padding:12px 20px;background:#135d67;color:white;text-align:center;text-decoration:none">NIVEL 2 — GASTAR CON SENTIDO →</a>'
            import re
            html = re.sub(r'(<body[^>]*>)', lambda m: m.group(1) + link, html, count=1, flags=re.I)
            response.set_data(html)
        if request.path.startswith('/nivel2'):
            for key in list(response.headers):
                if key[0].lower().startswith('access-control-'): del response.headers[key[0]]
            response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'"
        return response
    # Flask runs hooks in reverse registration order; strip CORS after base hooks.
    app.after_request_funcs.setdefault(None, []).insert(0, isolate_n2)
