"""Isolated preview entrypoint, also useful for integration tests."""
from flask import Flask
from .web import register

app = Flask(__name__)
register(app)

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '8000')), debug=False)
