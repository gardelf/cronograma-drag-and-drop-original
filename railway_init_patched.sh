#!/bin/bash
set -e

# Keep the existing Railway initialization and production patches, but make the
# final Flask process use the patched financial-panel entrypoint.
python3.11 -m py_compile web_server_patched.py
python3.11 - <<'PY'
from pathlib import Path

path = Path('railway_init.sh')
text = path.read_text(encoding='utf-8')
old = 'python3.11 web_server.py\n'
new = 'python3.11 web_server_patched.py\n'
if old not in text and new not in text:
    raise SystemExit('Could not find web_server.py startup line in railway_init.sh')
path.write_text(text.replace(old, new), encoding='utf-8')
PY

exec bash railway_init.sh
