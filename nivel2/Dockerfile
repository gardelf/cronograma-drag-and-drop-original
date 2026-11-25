FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/nivel2
CMD ["sh", "-c", "python -c 'from nivel2.db import migrate; migrate()' && gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60 nivel2.standalone:app"]
