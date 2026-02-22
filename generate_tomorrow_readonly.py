#!/usr/bin/env python3.11
"""
Wrapper script to generate tomorrow's cronograma in readonly mode
"""
import subprocess
import sys

# Run the main generator with --tomorrow flag
result = subprocess.run(
    ['python3.11', 'cronograma_generator_v7_5.py', '--tomorrow'],
    capture_output=True,
    text=True
)

# Print output
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)

sys.exit(result.returncode)
