from decimal import Decimal
import pytest
from nivel2.engine import eligible, money, propose, signature, validate_allocations
from nivel2.sync import FireflyReader, normalize

def tx(**kw):
    return dict(dict(movement_type='withdrawal',source_id='1',destination_id='2',description='Comida en Maroma',merchant='Cash',financial_category='Ocio',amount='30.00',currency='EUR'),**kw)

def test_suggestion_is_not_confirmation_and_no_invented_experience():
    result=propose(tx(),[{'id':'H02','standard_cost':30}])
    assert result['status']=='proposed'
    assert result['allocations']==[{'unit_id':'H02','amount':'30.00','obligation':'desconocido'}]
    assert 'hours' not in result and 'satisfaction' not in result

@pytest.mark.parametrize('kind,source,dest',[('deposit','1','2'),('transfer','6','7'),('withdrawal','9','2')])
def test_non_consumption(kind,source,dest):
    assert not eligible(tx(movement_type=kind,source_id=source,destination_id=dest))

@pytest.mark.parametrize('value',[None,'NaN','Infinity','-1','1.001'])
def test_invalid_money(value):
    with pytest.raises(ValueError): money(value)

def test_split_exact_decimal_and_unknown_not_zero():
    rows=[{'unit_id':'C01','amount':'0.10','obligation':'discrecional'},{'unit_id':'C02','amount':'0.20','obligation':'desconocido'}]
    validate_allocations(rows,'0.30',{'C01','C02'})
    with pytest.raises(ValueError): validate_allocations(rows,'0.31',{'C01','C02'})
    with pytest.raises(ValueError): validate_allocations(rows+rows,'0.60',{'C01','C02'})

def test_learned_rule_narrow_and_requires_confirmation():
    t=tx();assert signature(t)!=signature(tx(amount='31.00'))
    assert signature(t)!=signature(tx(source_id='6'))
    r=propose(t,[{'id':'C01'}],{'unit_id':'C01','obligation':'discrecional'})
    assert r['status']=='proposed' and r['confidence']==.95

def test_pagination_and_malformed_response(monkeypatch):
    monkeypatch.setenv('FIREFLY_URL','https://example.test');monkeypatch.setenv('FIREFLY_TOKEN','test')
    reader=FireflyReader();calls=[]
    def get(endpoint,params):
        calls.append(params['page']);return {'data':[{'id':str(params['page'])}],'meta':{'pagination':{'current_page':params['page'],'total_pages':2}}}
    monkeypatch.setattr(reader,'get',get)
    assert len(reader.transactions('2026-01-01','2026-01-31'))==2 and calls==[1,2]
    monkeypatch.setattr(reader,'get',lambda *a:{'data':[]})
    with pytest.raises(ValueError):reader.transactions('2026-01-01','2026-01-31')

def test_stable_journal_required():
    with pytest.raises(ValueError):normalize({'id':'1'},{'date':'2026-01-01'})
