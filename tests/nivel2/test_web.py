import base64
from flask import Flask
from nivel2.web import register

def client(monkeypatch):
    monkeypatch.setenv('NIVEL2_ACCESS_TOKEN','test-secret')
    app=Flask(__name__)
    @app.get('/api/personal')
    def personal(): return {'monthly_goal':3000,'daily_budget':50}
    @app.get('/sandbox')
    def sandbox(): return '<html><body>Existing financial panel</body></html>'
    @app.after_request
    def cors(r):r.headers['Access-Control-Allow-Origin']='*';return r
    register(app);return app.test_client()

AUTH={'Authorization':'Basic '+base64.b64encode(b'nivel2:test-secret').decode()}

def test_auth_csrf_and_level1_unchanged(monkeypatch):
    c=client(monkeypatch)
    assert c.get('/api/personal').json=={'monthly_goal':3000,'daily_budget':50}
    assert c.get('/nivel2').status_code==401
    r=c.get('/nivel2',headers=AUTH)
    assert r.status_code==200 and 'Access-Control-Allow-Origin' not in r.headers
    assert r.headers['Cache-Control']=='no-store'
    assert c.get('/api/personal').headers['Access-Control-Allow-Origin']=='*'
    assert c.post('/nivel2/api/units',headers=AUTH,json={}).status_code==403
    assert c.post('/nivel2/api/units',headers={**AUTH,'X-Nivel2-Request':'1','Origin':'https://evil.test'},json={}).status_code==403
    assert b'/nivel2' in c.get('/sandbox').data

def test_no_token_fails_closed(monkeypatch):
    c=client(monkeypatch);monkeypatch.delenv('NIVEL2_ACCESS_TOKEN')
    assert c.get('/nivel2',headers=AUTH).status_code==503
    assert c.get('/api/personal').status_code==200
