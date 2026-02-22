import glob
import os
from datetime import datetime

base_dir = '/app' if os.path.exists('/app') else os.path.dirname(os.path.abspath(__file__))
pattern = os.path.join(base_dir, 'cronograma_v7_5_*.html')
html_files = glob.glob(pattern)

print(f"Base dir: {base_dir}")
print(f"Pattern: {pattern}")
print(f"Found {len(html_files)} files:")

for f in sorted(html_files, key=os.path.getmtime, reverse=True):
    mtime = os.path.getmtime(f)
    mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    print(f"  {mtime_str} - {os.path.basename(f)}")

if html_files:
    latest = max(html_files, key=os.path.getmtime)
    print(f"\nLatest file: {latest}")
