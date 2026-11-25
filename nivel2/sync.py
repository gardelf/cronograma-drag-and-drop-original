"""GET-only import. Short overlapping window; daily full history reconciliation."""
import hashlib
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit
import requests
from psycopg2.extras import Json
from .db import connect, migrate
from .engine import eligible, money, propose, signature

class FireflyReader:
    def __init__(self):
        self.base=os.environ['FIREFLY_URL'].rstrip('/')
        if urlsplit(self.base).scheme!='https': raise ValueError('Firefly must use HTTPS')
        self.token=os.environ.get('NIVEL2_FIREFLY_TOKEN') or os.environ['FIREFLY_TOKEN']

    def get(self, endpoint, params=None, missing_ok=False):
        r=requests.get(self.base+'/api/v1/'+endpoint,headers={'Authorization':'Bearer '+self.token,'Accept':'application/json'},params=params,timeout=30,allow_redirects=False)
        if missing_ok and r.status_code==404: return None
        if not 200<=r.status_code<300: raise RuntimeError('firefly_http_'+str(r.status_code))
        return r.json()

    def transactions(self,start,end):
        rows=[]; page=1
        while True:
            data=self.get('transactions',{'start':str(start),'end':str(end),'page':page,'limit':100})
            if not isinstance(data.get('data'),list): raise ValueError('invalid_firefly_response')
            pagination=data.get('meta',{}).get('pagination',{})
            if int(pagination.get('current_page',0))!=page: raise ValueError('invalid_pagination')
            total=int(pagination['total_pages'])
            rows.extend(data['data'])
            if page>=total: return rows
            page+=1
            if page>10000: raise ValueError('pagination_limit')

def normalize(group, trans):
    journal=str(trans.get('transaction_journal_id') or '')
    if not journal: raise ValueError('missing_stable_journal_id')
    raw={k:trans.get(k) for k in ('date','description','amount','currency_code','category_name','destination_name','source_id','destination_id','type')}
    return dict(journal_id=journal,group_id=str(group['id']),occurred_on=date.fromisoformat(str(trans['date'])[:10]),
        description=trans.get('description') or '',amount=money(abs(__import__('decimal').Decimal(str(trans['amount'])))),
        currency=trans.get('currency_code') or 'UNKNOWN',financial_category=trans.get('category_name'),merchant=trans.get('destination_name'),
        source_id=str(trans.get('source_id') or ''),destination_id=str(trans.get('destination_id') or ''),movement_type=trans.get('type') or '',
        fingerprint=hashlib.sha256(json.dumps(raw,sort_keys=True).encode()).hexdigest(),raw=raw)

def save_transaction(cur,instance,tx,units):
    cur.execute('SELECT * FROM n2_transactions WHERE source_instance=%s AND journal_id=%s FOR UPDATE',(instance,tx['journal_id']))
    old=cur.fetchone()
    if old and old['fingerprint']==tx['fingerprint'] and not old['deleted']: return old['id']
    cur.execute('SELECT * FROM n2_rules WHERE signature=%s',(signature(tx),)); rule=cur.fetchone()
    result=propose(tx,units,rule)
    if old and old['status'] in ('confirmed','review'):
        result.update(status='review' if eligible(tx) else 'excluded',confidence=0,reason='El original cambió; revisar imputaciones conservadas')
    values=[instance]+[tx[k] for k in ('journal_id','group_id','occurred_on','description','amount','currency','financial_category','merchant','source_id','destination_id','movement_type','fingerprint')]+[Json(tx['raw']),eligible(tx),result['status'],result['confidence'],result['reason']]
    cur.execute('''INSERT INTO n2_transactions(source_instance,journal_id,group_id,occurred_on,description,amount,currency,financial_category,merchant,source_id,destination_id,movement_type,fingerprint,raw,eligible,status,confidence,reason)
      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
      ON CONFLICT(source_instance,journal_id) DO UPDATE SET group_id=EXCLUDED.group_id,occurred_on=EXCLUDED.occurred_on,description=EXCLUDED.description,amount=EXCLUDED.amount,currency=EXCLUDED.currency,financial_category=EXCLUDED.financial_category,merchant=EXCLUDED.merchant,source_id=EXCLUDED.source_id,destination_id=EXCLUDED.destination_id,movement_type=EXCLUDED.movement_type,fingerprint=EXCLUDED.fingerprint,raw=EXCLUDED.raw,eligible=EXCLUDED.eligible,status=EXCLUDED.status,confidence=EXCLUDED.confidence,reason=EXCLUDED.reason,deleted=false,version=n2_transactions.version+1,updated_at=now() RETURNING id''',values)
    tid=cur.fetchone()['id']
    if old:
        cur.execute('INSERT INTO n2_corrections(transaction_id,action,before_data,after_data) VALUES (%s,%s,%s,%s)',(tid,'source_update',Json(old['raw']),Json(tx['raw'])))
    if not old or old['status'] not in ('confirmed','review'):
        cur.execute('DELETE FROM n2_allocations WHERE transaction_id=%s',(tid,))
        for a in result['allocations']:
            cur.execute('INSERT INTO n2_allocations(transaction_id,unit_id,amount,obligation) VALUES (%s,%s,%s,%s)',(tid,a['unit_id'],a['amount'],a['obligation']))
    return tid

def run_sync(reader=None,force_full=False):
    reader=reader or FireflyReader()
    instance=reader.base
    today=datetime.now(timezone.utc).date()
    historical_start=date.fromisoformat(os.getenv('NIVEL2_HISTORY_START','2025-09-01'))
    if historical_start>today: raise ValueError('history_start_in_future')
    with connect() as lock:
        with lock.cursor() as cur:
            cur.execute('SELECT pg_try_advisory_lock(26251102) AS acquired')
            if not cur.fetchone()['acquired']: return {'status':'busy'}
            cur.execute('SELECT key,value FROM n2_state'); state={r['key']:r['value'] for r in cur.fetchall()}
            if state.get('source_instance',instance)!=instance: raise ValueError('source_instance_changed')
            full=force_full or state.get('full_day')!=str(today) or state.get('history_start')!=str(historical_start)
            start=historical_start if full else max(historical_start,today-timedelta(days=7))
            cur.execute("INSERT INTO n2_sync_runs(status) VALUES ('running') RETURNING id"); run_id=cur.fetchone()['id']
        lock.commit()
        try:
            # Obtain every page before any removal or cursor advancement.
            groups=reader.transactions(start,today)
            txs=[normalize(g,t) for g in groups for t in g['attributes']['transactions']]
            seen={t['journal_id'] for t in txs}
            with lock.cursor() as cur:
                cur.execute('SELECT * FROM n2_transactions WHERE source_instance=%s AND occurred_on BETWEEN %s AND %s AND deleted=false',(instance,start,today))
                missing=[r for r in cur.fetchall() if r['journal_id'] not in seen]
            deleted=[]
            # Confirm absence using the original group, never infer deletion from a partial list.
            details={}
            for row in missing:
                gid=row['group_id']
                if gid not in details: details[gid]=reader.get('transactions/'+gid,missing_ok=True)
                data=details[gid]
                children=[] if data is None else [normalize(data['data'],t) for t in data['data']['attributes']['transactions']]
                match=next((t for t in children if t['journal_id']==row['journal_id']),None)
                if match: txs.append(match)
                else: deleted.append(row['id'])
            with lock.cursor() as cur:
                cur.execute('SELECT * FROM n2_units'); units=cur.fetchall()
                for tx in txs: save_transaction(cur,instance,tx,units)
                for tid in deleted:
                    cur.execute("UPDATE n2_transactions SET deleted=true,status='review',reason='Original eliminado en Firefly; historial conservado',version=version+1 WHERE id=%s",(tid,))
                    cur.execute("INSERT INTO n2_corrections(transaction_id,action,before_data,after_data) VALUES (%s,'source_deleted','{}','{}')",(tid,))
                updates={'source_instance':instance,'last_sync':datetime.now(timezone.utc).isoformat(),'history_start':str(historical_start)}
                if full: updates['full_day']=str(today)
                for k,v in updates.items(): cur.execute('INSERT INTO n2_state VALUES (%s,%s) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value',(k,v))
                cur.execute("UPDATE n2_sync_runs SET status='success',finished_at=now(),scanned=%s WHERE id=%s",(len(txs),run_id))
            lock.commit()
            return {'status':'success','scanned':len(txs),'full':full}
        except Exception as exc:
            lock.rollback()
            with lock.cursor() as cur:
                # Persist type only: never URLs, credentials or raw HTTP bodies.
                cur.execute("UPDATE n2_sync_runs SET status='error',finished_at=now(),error_code=%s WHERE id=%s",(type(exc).__name__,run_id))
            lock.commit()
            raise
        finally:
            with lock.cursor() as cur: cur.execute('SELECT pg_advisory_unlock(26251102)')

def worker():
    migrate()
    while True:
        try: run_sync()
        except Exception as exc: print('Nivel2 sync error:',type(exc).__name__,flush=True)
        time.sleep(max(60,int(os.getenv('NIVEL2_SYNC_SECONDS','900'))))

if __name__=='__main__':
    import sys
    if '--once' in sys.argv:
        migrate(); print(run_sync(force_full='--full' in sys.argv))
    else: worker()
