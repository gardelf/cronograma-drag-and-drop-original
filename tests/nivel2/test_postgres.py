"""Integration tests only against a disposable database explicitly marked for tests."""
import os
from datetime import date
import pytest
from nivel2.db import connect, migrate
from nivel2.sync import run_sync
from test_web import client, AUTH

pytestmark=pytest.mark.skipif(os.getenv('NIVEL2_TEST_DATABASE')!='1',reason='Disposable PostgreSQL required')

@pytest.fixture(autouse=True)
def clean(monkeypatch):
    monkeypatch.setenv('NIVEL2_HISTORY_START','2025-09-01')
    with connect() as c,c.cursor() as q:
        q.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public')
    migrate()

def group(amount='30.00',description='Comida Maroma',kind='withdrawal',jid='11'):
    return {'id':'1','attributes':{'transactions':[{'transaction_journal_id':jid,'date':'2026-01-15T12:00:00+01:00','description':description,'amount':amount,'currency_code':'EUR','category_name':'Ocio','destination_name':'Cash','source_id':'1','destination_id':'2','type':kind}]}}

class Reader:
    base='https://firefly.example.test'
    def __init__(self,groups):self.groups=groups
    def transactions(self,*args):return self.groups
    def get(self,*args,**kw):return {'data':self.groups[0]} if self.groups else None

def query(sql,params=()):
    with connect() as c,c.cursor() as q:q.execute(sql,params);return q.fetchall()

def post(c,path,data):return c.post('/nivel2/api/'+path,headers={**AUTH,'X-Nivel2-Request':'1'},json=data)

def test_migrations_seed_and_edit_preservation(monkeypatch):
    migrate();assert len(query('SELECT * FROM n2_units'))==20
    assert len(query('SELECT * FROM n2_values'))==5
    assert query("SELECT standard_cost,satisfaction,hours FROM n2_units WHERE id='C01'")[0]==dict(standard_cost=None,satisfaction=None,hours=None)
    c=client(monkeypatch);u=next(u for u in c.get('/nivel2/api/matrix',headers=AUTH).json['units'] if u['id']=='E01')
    u['name']='Trekking editado';assert post(c,'units',u).status_code==200
    migrate();assert query("SELECT name FROM n2_units WHERE id='E01'")[0]['name']=='Trekking editado'
    assert post(c,'units',u).status_code==409
    assert query("SELECT name FROM n2_units WHERE id='R05'")[0]['name']=='Plaza de garaje 39'

def test_idempotency_split_learning_changes_and_deletion(monkeypatch):
    r=Reader([group()]);run_sync(r,True);run_sync(r,True)
    assert len(query('SELECT * FROM n2_transactions'))==1
    t=query('SELECT * FROM n2_transactions')[0];assert t['status']=='proposed'
    c=client(monkeypatch)
    path='transactions/'+str(t['id'])+'/confirm'
    invalid={'version':t['version'],'allocations':[{'unit_id':'H02','amount':'29','obligation':'discrecional'}]}
    assert post(c,path,invalid).status_code==400
    valid={'version':t['version'],'allocations':[{'unit_id':'H02','amount':'20','obligation':'discrecional'},{'unit_id':'C01','amount':'10','obligation':'desconocido'}]}
    assert post(c,path,valid).status_code==200
    assert post(c,path,valid).status_code==409
    summary=c.get('/nivel2/api/summary?start=2026-01-01&end=2026-01-31',headers=AUTH).json
    assert len(summary['items'])==2
    assert sum(float(x['amount']) for x in summary['items'])==30
    run_sync(r,True);assert query('SELECT status FROM n2_transactions')[0]['status']=='confirmed'
    r.groups=[group('35.00')];run_sync(r,True)
    assert query('SELECT status FROM n2_transactions')[0]['status']=='review'
    assert len(query('SELECT * FROM n2_allocations'))==2
    assert not c.get('/nivel2/api/summary?start=2026-01-01&end=2026-01-31',headers=AUTH).json['items']
    r.groups=[];run_sync(r,True);assert query('SELECT deleted FROM n2_transactions')[0]['deleted']
    assert len(query('SELECT * FROM n2_corrections'))==3

def test_confirmed_rule_persists_but_new_journal_needs_confirmation(monkeypatch):
    r=Reader([group()]);run_sync(r,True);t=query('SELECT * FROM n2_transactions')[0];c=client(monkeypatch)
    assert post(c,'transactions/'+str(t['id'])+'/confirm',{'version':t['version'],'allocations':[{'unit_id':'H02','amount':'30.00','obligation':'discrecional'}]}).status_code==200
    r.groups=[group(),group(jid='12')];run_sync(r,True)
    t=query("SELECT * FROM n2_transactions WHERE journal_id='12'")[0]
    assert t['status']=='proposed' and float(t['confidence'])==.95

def test_failed_read_does_not_delete_or_advance_state():
    r=Reader([group()]);run_sync(r,True);before=query('SELECT * FROM n2_state ORDER BY key')
    def fail(*args):raise RuntimeError('HTTP failed')
    r.transactions=fail
    with pytest.raises(RuntimeError):run_sync(r,True)
    assert not query('SELECT deleted FROM n2_transactions')[0]['deleted']
    assert before==query('SELECT * FROM n2_state ORDER BY key')
    assert query('SELECT status,error_code FROM n2_sync_runs ORDER BY id DESC LIMIT 1')[0]=={'status':'error','error_code':'RuntimeError'}

def test_deposit_not_allocated_and_moved_date_not_deleted():
    r=Reader([group(kind='deposit')]);run_sync(r,True)
    assert query('SELECT status FROM n2_transactions')[0]['status']=='excluded'
    assert not query('SELECT * FROM n2_allocations')
    moved=group();moved['attributes']['transactions'][0]['date']='2025-01-01T12:00:00+01:00'
    r.groups=[];r.get=lambda *a,**kw:{'data':moved}
    run_sync(r,True)
    t=query('SELECT * FROM n2_transactions')[0]
    assert not t['deleted'] and t['occurred_on']==date(2025,1,1)
