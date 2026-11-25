"""The two additions must not alter a single existing Level 1 source byte."""
import subprocess
from pathlib import Path
import pytest

BASE='3a1454ff0f3e2ff1369a2c11493b4fb0830f5453'

@pytest.mark.parametrize('path,addition',[
 ('web_server.py',"if os.environ.get('NIVEL2_ENABLED') == '1':\n    from nivel2.web import register as register_nivel2\n    register_nivel2(app)\n\n"),
 ('web_server_patched.py','import os as _n2_os\nif _n2_os.environ.get("NIVEL2_ENABLED") == "1":\n    from nivel2.web import register as _register_nivel2\n    _register_nivel2(app)\n\n'),
])
def test_level1_source_is_preserved(path,addition):
    result=subprocess.run(['git','show',BASE+':'+path],capture_output=True,text=True)
    if result.returncode:
        if __import__('os').getenv('CI'): pytest.fail('Cannot read regression baseline')
        pytest.skip('Full GitHub checkout required for baseline')
    current=Path(path).read_text()
    assert current.count(addition)==1
    assert current.replace(addition,'',1)==result.stdout
