"""
Configuration module for Cronograma
Loads environment variables and provides configuration functions
"""

import os
from pathlib import Path

def get_config():
    """Get configuration from environment variables"""
    return {
        'TODOIST_API_TOKEN': os.environ.get('TODOIST_API_TOKEN', ''),
        'ICLOUD_USERNAME': os.environ.get('ICLOUD_USERNAME', ''),
        'ICLOUD_APP_PASSWORD': os.environ.get('ICLOUD_APP_PASSWORD', ''),
        'FIREFLY_URL': os.environ.get('FIREFLY_URL', ''),
        'FIREFLY_TOKEN': os.environ.get('FIREFLY_TOKEN', ''),
        'DATABASE_URL': os.environ.get('DATABASE_URL', ''),
        'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', ''),
    }

def load_env_file(env_file='.env'):
    """Load environment variables from a .env file"""
    env_path = Path(env_file)
    if not env_path.exists():
        return
    
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ[key] = value
