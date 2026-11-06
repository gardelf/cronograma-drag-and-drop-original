#!/bin/bash
# Railway initialization script

echo "🚀 Inicializando sistema de cronograma automatizado..."

# Remove any .env file to ensure Railway environment variables are used
if [ -f ".env" ]; then
    echo "🗑️  Eliminando archivo .env local para usar variables de Railway..."
    rm -f .env
fi

# Apply production patch for Patrimonio panel before starting the app.
# Patrimonio panel must show real current-month Firefly transactions from account 6 to account 7,
# not configured recurrences/automations. The financial panel must exclude those property movements.
# It also calculates the annual projected property cost from active Firefly recurrences on route 6 -> 7,
# but the header only displays the current month and annualized monthly average.
echo "🏠 Aplicando parches Firefly para separar patrimonio y gastos personales..."
python3.11 - <<'PY'
from pathlib import Path
import re

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

if 'def get_account_route_recurring_annual_total' not in firefly_text:
    annual_method = '''
    def get_account_route_recurring_annual_total(self, source_account_id, destination_account_id):
        """Return annual projected total for active Firefly recurrences on one account route."""
        try:
            expected_source = str(source_account_id)
            expected_destination = str(destination_account_id)
            data = self._make_request('recurrences')
            if not data or 'data' not in data:
                return {'items': [], 'total': 0.0}

            def multiplier_for_repetition(rep):
                freq = str(rep.get('type') or rep.get('frequency') or '').lower()
                raw_skip = rep.get('skip') or rep.get('interval') or rep.get('period') or 0
                try:
                    skip = int(raw_skip or 0)
                except Exception:
                    skip = 0
                every = skip if skip and skip > 0 else 1
                if freq in ('yearly', 'annual'):
                    return 1.0
                if freq in ('half-year', 'half_year', 'semi-yearly', 'semi_yearly'):
                    return 2.0
                if freq in ('quarterly', 'quarter'):
                    return 4.0
                if freq in ('weekly',):
                    return 52.0 / every
                if freq in ('monthly', 'ndom'):
                    return 12.0 / every
                if 'year' in freq:
                    return 1.0
                if 'quarter' in freq or 'trim' in freq:
                    return 4.0
                if 'month' in freq:
                    return 12.0 / every
                if 'week' in freq:
                    return 52.0 / every
                return 1.0

            items = []
            total = 0.0
            for recurrence in data['data']:
                attrs = recurrence.get('attributes', {})
                if attrs.get('active') is False:
                    continue
                repetitions = attrs.get('repetitions') or [{}]
                multiplier = max(multiplier_for_repetition(repetitions[0] or {}), 0)
                title = attrs.get('title') or attrs.get('description') or ''

                for tx in attrs.get('transactions', []):
                    source_id = str(tx.get('source_id') or '')
                    destination_id = str(tx.get('destination_id') or '')
                    if source_id != expected_source or destination_id != expected_destination:
                        continue
                    amount = abs(float(tx.get('amount', 0) or 0))
                    if amount == 0:
                        continue
                    annual_amount = amount * multiplier
                    items.append({
                        'id': recurrence.get('id'),
                        'title': title,
                        'description': tx.get('description') or title,
                        'amount': round(amount, 2),
                        'annual_amount': round(annual_amount, 2),
                        'frequency': (repetitions[0] or {}).get('type') or '',
                        'multiplier': multiplier,
                        'source_id': source_id,
                        'source_name': tx.get('source_name', ''),
                        'destination_id': destination_id,
                        'destination_name': tx.get('destination_name', ''),
                    })
                    total += annual_amount

            items.sort(key=lambda item: (item.get('title') or item.get('description') or '').lower())
            return {'items': items, 'total': round(total, 2)}
        except Exception as e:
            print(f"Error getting annual account route recurrences: {e}")
            return {'items': [], 'total': 0.0}
'''
    marker = '    def get_extraordinary_expenses_current_month(self, year, month):\n'
    firefly_text = firefly_text.replace(marker, annual_method + '\n' + marker)

firefly.write_text(firefly_text, encoding='utf-8')

web_text = web_server.read_text(encoding='utf-8')
web_text = web_text.replace('"""Current-month recurring transfers from Patrimonio to Caixa Propiedades."""','"""Current-month real transactions from Patrimonio to Caixa Propiedades."""')
web_text = web_text.replace('data = FireflyClient().get_recurring_transfers_for_month(','data = FireflyClient().get_account_route_transactions_for_month(')
web_text = web_text.replace("        data = FireflyClient().get_account_route_transactions_for_month(\n            now.year,\n            now.month,\n            source_account_id=6,\n            destination_account_id=7,\n        )","        client = FireflyClient()\n        data = client.get_account_route_transactions_for_month(\n            now.year,\n            now.month,\n            source_account_id=6,\n            destination_account_id=7,\n        )\n        annual = client.get_account_route_recurring_annual_total(6, 7)")
web_text = web_text.replace("                'items': data.get('items', []),\n                'source': {'id': 6, 'name': 'Patrimonio'},","                'items': data.get('items', []),\n                'annual_total': annual.get('total', 0.0),\n                'annual_monthly_average': round(annual.get('total', 0.0) / 12, 2),\n                'annual_items': annual.get('items', []),\n                'source': {'id': 6, 'name': 'Patrimonio'},")
web_text = web_text.replace("                    if trans.get('type') == 'withdrawal':\n                        transactions.append({","                    if trans.get('type') == 'withdrawal':\n                        source_id = str(trans.get('source_id') or '')\n                        destination_id = str(trans.get('destination_id') or '')\n                        if source_id == '6' and destination_id == '7':\n                            continue\n                        transactions.append({")
web_text = web_text.replace("        monthly_expenses = current_month.get('expenses', 0)\n        monthly_goal = 3000.0","        property_data = client.get_account_route_transactions_for_month(now.year, now.month, 6, 7)\n        property_expenses = property_data.get('total', 0.0)\n        monthly_expenses = max(current_month.get('expenses', 0) - property_expenses, 0)\n        monthly_goal = 3000.0")
web_server.write_text(web_text, encoding='utf-8')

html = sandbox.read_text(encoding='utf-8')
html = html.replace('Automatizaciones activas de Firefly<br>Cuenta 6 → Cuenta 7','Transacciones registradas en Firefly<br>Cuenta 6 → Cuenta 7')
html = html.replace('Sin movimientos programados para este mes.','Sin transacciones registradas para este mes.')
html = html.replace('const dailyBudget = Math.floor(remaining / Math.max(mp.days_remaining || 1, 1));','const dailyBudget = Math.floor((mp.discretionary_goal || 1900) / (mp.days_in_month || 30));')
property_header = '''let html = `
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:${items.length ? '18px' : '0'};">
                <div style="flex:1;min-width:0;">
                    <div class="section-label" style="margin-bottom:6px;">Total del mes vigente</div>
                    <div style="font-size:clamp(20px, 5vw, 26px);font-weight:800;color:var(--accent-blue);line-height:1.05;white-space:nowrap;">${fmtEur(data.total || 0)}</div>
                </div>
                <div style="flex:1;min-width:0;text-align:center;">
                    <div class="section-label" style="margin-bottom:6px;">Media mensual anualizada</div>
                    <div style="font-size:clamp(18px, 4.5vw, 24px);font-weight:800;color:var(--accent-purple);line-height:1.05;white-space:nowrap;">${fmtEur(data.annual_monthly_average || ((data.annual_total || 0) / 12))}</div>
                </div>
                <div style="flex:0 1 150px;font-size:11px;color:var(--text-muted);text-align:right;line-height:1.3;">
                    Transacciones registradas en Firefly<br>Cuenta 6 → Cuenta 7
                </div>
            </div>`;'''
html = re.sub(r"let html = `\s*<div style=\"display:flex;justify-content:space-between;align-items:center;gap:[^\"]*;margin-bottom:\$\{items\.length \? '18px' : '0'\};\">.*?</div>`;", property_header, html, count=1, flags=re.S)
html = html.replace("const label = item.description || item.title || 'Transferencia programada';\n                html += `<div style=\"display:flex;justify-content:space-between;gap:16px;padding:10px 12px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:var(--radius-md);\">\n                    <div>\n                        <div style=\"font-size:13px;font-weight:600;color:var(--text-primary);\">${label}</div>\n                        <div style=\"font-size:11px;color:var(--text-muted);margin-top:2px;\">${item.frequency || 'recurrente'}</div>","const label = item.description || item.title || 'Transacción registrada';\n                const detail = [item.date, item.category].filter(Boolean).join(' · ') || 'registrada';\n                html += `<div style=\"display:flex;justify-content:space-between;gap:16px;padding:10px 12px;background:var(--bg-secondary);border:1px solid var(--border);border-radius:var(--radius-md);\">\n                    <div>\n                        <div style=\"font-size:13px;font-weight:600;color:var(--text-primary);\">${label}</div>\n                        <div style=\"font-size:11px;color:var(--text-muted);margin-top:2px;\">${detail}</div>")
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
