#!/bin/bash
# Railway initialization script

echo "🚀 Inicializando sistema de cronograma automatizado..."

# Remove any .env file to ensure Railway environment variables are used
if [ -f ".env" ]; then
    echo "🗑️  Eliminando archivo .env local para usar variables de Railway..."
    rm -f .env
fi

# Apply production patch for Patrimonio panel and fixed expenses before starting the app.
# Patrimonio panel must show real current-month Firefly transactions from account 6 to account 7,
# not configured recurrences/automations. Fixed expenses must only include Fernando Garrido → Cash.
echo "🏠 Aplicando parches Firefly para panel financiero..."
python3.11 - <<'PY'
from pathlib import Path

firefly = Path('firefly_client.py')
web_server = Path('web_server.py')
sandbox = Path('templates/sandbox.html')

firefly_text = firefly.read_text(encoding='utf-8')
if 'def get_account_route_transactions_for_month' not in firefly_text:
    method = '''
    def get_account_route_transactions_for_month(self, year, month, source_account_id, destination_account_id):
        """Return real transactions for one exact account route and month."""
        try:
            import calendar

            start_date = datetime(year, month, 1)
            last_day = calendar.monthrange(year, month)[1]
            end_date = datetime(year, month, last_day)
            expected_source = str(source_account_id)
            expected_destination = str(destination_account_id)

            data = self._make_request('transactions', params={
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d'),
            })
            if not data or 'data' not in data:
                return {'items': [], 'total': 0.0}

            items = []
            total = 0.0
            for transaction in data['data']:
                attrs = transaction.get('attributes', {})
                group_id = transaction.get('id')
                for trans in attrs.get('transactions', []):
                    source_id = trans.get('source_id')
                    destination_id = trans.get('destination_id')
                    if str(source_id or '') != expected_source:
                        continue
                    if str(destination_id or '') != expected_destination:
                        continue

                    amount = abs(float(trans.get('amount', 0) or 0))
                    if amount == 0:
                        continue

                    items.append({
                        'id': trans.get('transaction_journal_id') or trans.get('id') or group_id,
                        'description': trans.get('description', ''),
                        'amount': round(amount, 2),
                        'date': (trans.get('date', '') or '')[:10],
                        'type': trans.get('type', ''),
                        'category': trans.get('category_name') or '',
                        'source_id': source_id,
                        'source_name': trans.get('source_name', ''),
                        'destination_id': destination_id,
                        'destination_name': trans.get('destination_name', ''),
                    })
                    total += amount

            items.sort(key=lambda item: (item.get('date') or '', item.get('description') or ''), reverse=True)
            return {'items': items, 'total': round(total, 2)}
        except Exception as e:
            print(f"Error getting account route transactions: {e}")
            return {'items': [], 'total': 0.0}
'''
    marker = '    def get_extraordinary_expenses_current_month(self, year, month):\n'
    firefly_text = firefly_text.replace(marker, method + '\n' + marker)

if "expected_source_name = 'Fernando Garrido'" not in firefly_text:
    firefly_text = firefly_text.replace(
        "            items = []\n            total = 0.0\n\n            for rec in data['data']:",
        "            items = []\n            total = 0.0\n            expected_source_id = '1'\n            expected_destination_id = '2'\n            expected_source_name = 'Fernando Garrido'\n            expected_destination_name = 'Cash'\n\n            for rec in data['data']:"
    )
    firefly_text = firefly_text.replace(
        "                for tx in txs:\n                    if tx.get('type', '') not in ('withdrawal', ''):\n                        continue\n                    amt = abs(float(tx.get('amount', 0) or 0))",
        "                for tx in txs:\n                    if tx.get('type', '') not in ('withdrawal', ''):\n                        continue\n                    source_id = str(tx.get('source_id') or '')\n                    destination_id = str(tx.get('destination_id') or '')\n                    source_name = tx.get('source_name') or ''\n                    destination_name = tx.get('destination_name') or ''\n                    if source_id and source_id != expected_source_id:\n                        continue\n                    if destination_id and destination_id != expected_destination_id:\n                        continue\n                    if not source_id and source_name != expected_source_name:\n                        continue\n                    if not destination_id and destination_name != expected_destination_name:\n                        continue\n                    amt = abs(float(tx.get('amount', 0) or 0))"
    )
    firefly_text = firefly_text.replace(
        "                                'tags': tx.get('tags', []),\n                            }",
        "                                'tags': tx.get('tags', []),\n                                'source_id': tx.get('source_id'),\n                                'source_name': source_name,\n                                'destination_id': tx.get('destination_id'),\n                                'destination_name': destination_name,\n                            }"
    )

firefly.write_text(firefly_text, encoding='utf-8')

web_text = web_server.read_text(encoding='utf-8')
web_text = web_text.replace(
    '"""Current-month recurring transfers from Patrimonio to Caixa Propiedades."""',
    '"""Current-month real transactions from Patrimonio to Caixa Propiedades."""'
)
web_text = web_text.replace(
    'data = FireflyClient().get_recurring_transfers_for_month(',
    'data = FireflyClient().get_account_route_transactions_for_month('
)
web_server.write_text(web_text, encoding='utf-8')

html = sandbox.read_text(encoding='utf-8')
html = html.replace(
    'Automatizaciones activas de Firefly<br>Cuenta 6 → Cuenta 7',
    'Transacciones registradas en Firefly<br>Cuenta 6 → Cuenta 7'
)
html = html.replace(
    'Sin movimientos programados para este mes.',
    'Sin transacciones registradas para este mes.'
)
html = html.replace(
    "const label = item.description || item.title || 'Transferencia programada';\n                html += `<div style=\"display:flex;justify-content:space-between;gap:16px;padding:10px 12px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:var(--radius-md);\">\n                    <div>\n                        <div style=\"font-size:13px;font-weight:600;color:var(--text-primary);\">${label}</div>\n                        <div style=\"font-size:11px;color:var(--text-muted);margin-top:2px;\">${item.frequency || 'recurrente'}</div>",
    "const label = item.description || item.title || 'Transacción registrada';\n                const detail = [item.date, item.category].filter(Boolean).join(' · ') || 'registrada';\n                html += `<div style=\"display:flex;justify-content:space-between;gap:16px;padding:10px 12px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:var(--radius-md);\">\n                    <div>\n                        <div style=\"font-size:13px;font-weight:600;color:var(--text-primary);\">${label}</div>\n                        <div style=\"font-size:11px;color:var(--text-muted);margin-top:2px;\">${detail}</div>"
)
sandbox.write_text(html, encoding='utf-8')
PY

# Create database if it doesn't exist
if [ ! -f "events_tracker.db" ]; then
    echo "📊 Creando base de datos..."
    python3.11 -c "from events_db import init_db; init_db()"
fi

# Generate initial cronograma
echo "📅 Generando cronograma inicial..."
python3.11 cronograma_generator_v7_5.py || echo "⚠️  Advertencia: No se pudo generar cronograma inicial (se generará en la primera petición)"

echo "✅ Inicialización completada"
echo "🌐 Iniciando servidor web (incluye API de gastos)..."

# Start web server (includes expense API endpoints)
python3.11 web_server.py
