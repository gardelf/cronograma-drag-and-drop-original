"""
Patched entrypoint for Railway.

Imports the original Flask app and overrides the financial panel endpoints so
the discretionary total and its category breakdown use the same transaction set.
"""
from datetime import datetime, timedelta

from flask import jsonify

import web_server as original
from firefly_client import FireflyClient

app = original.app


def _month_range(year, month):
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1)
    else:
        end = datetime(year, month + 1, 1)
    end = end - timedelta(days=1)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


def _matches_fixed_item(trans, fixed_items):
    description = (trans.get("description") or "").lower().strip()
    if not description:
        return False
    for item in fixed_items or []:
        fixed_text = (item.get("title") or item.get("description") or "").lower().strip()
        if fixed_text and (description in fixed_text or fixed_text in description):
            return True
    return False


def _is_extraordinary(trans):
    return any(str(tag).lower() == "extraordinario" for tag in (trans.get("tags") or []))


def _is_property_route(trans):
    return str(trans.get("source_id") or "") == "6" and str(trans.get("destination_id") or "") == "7"


def _get_discretionary_expenses_for_month(client, year, month, fixed_items):
    start, end = _month_range(year, month)
    data = client._make_request("transactions", params={"start": start, "end": end})

    if not data or "data" not in data:
        return {"total": 0.0, "count": 0, "transactions": []}

    transactions = []
    for transaction in data["data"]:
        attrs = transaction.get("attributes", {})
        for trans in attrs.get("transactions", []):
            if trans.get("type") != "withdrawal":
                continue
            if _is_property_route(trans):
                continue
            if _is_extraordinary(trans):
                continue
            if _matches_fixed_item(trans, fixed_items):
                continue

            amount = abs(float(trans.get("amount", 0) or 0))
            if amount == 0:
                continue

            transactions.append({
                "date": (trans.get("date", "") or "")[:10],
                "description": trans.get("description", ""),
                "amount": round(amount, 2),
                "category": trans.get("category_name") or "Sin categoria",
                "tags": trans.get("tags", []),
            })

    transactions.sort(key=lambda item: item["date"])
    total = round(sum(item["amount"] for item in transactions), 2)
    return {"total": total, "count": len(transactions), "transactions": transactions}


def panel_gastos_mes_detalle_patched():
    try:
        client = FireflyClient()
        now = datetime.now()
        fixed_data = client.get_recurring_fixed_for_month(now.year, now.month)
        detail = _get_discretionary_expenses_for_month(
            client,
            now.year,
            now.month,
            fixed_data.get("items", []),
        )
        return jsonify({"success": True, **detail})
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


def panel_gastos_data_patched():
    try:
        client = FireflyClient()
        now = datetime.now()

        current_month = client.get_monthly_summary(now.year, now.month)

        if now.month == 1:
            prev_year = now.year - 1
            prev_month = 12
        else:
            prev_year = now.year
            prev_month = now.month - 1
        previous_month = client.get_monthly_summary(prev_year, prev_month)

        yesterday = client.get_yesterday_expenses()
        weekly = client.get_weekly_summary()
        weekly_detail = client.get_weekly_transactions_detail()
        extraordinary = client.get_extraordinary_expenses_next_month()

        import calendar
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        days_elapsed = now.day

        property_data = client.get_account_route_transactions_for_month(now.year, now.month, 6, 7)
        property_expenses = property_data.get("total", 0.0)
        monthly_expenses = max(current_month.get("expenses", 0) - property_expenses, 0)
        monthly_goal = 3000.0

        recurring_data = client.get_recurring_fixed_for_month(now.year, now.month)
        fixed_expenses = recurring_data.get("total", 0.0)
        fixed_items = recurring_data.get("items", [])

        extraordinary_data = client.get_extraordinary_expenses_current_month(now.year, now.month)
        extraordinary_expenses_current = extraordinary_data.get("total", 0.0)
        extraordinary_items_current = extraordinary_data.get("items", [])

        discretionary_data = _get_discretionary_expenses_for_month(client, now.year, now.month, fixed_items)
        discretionary_expenses = discretionary_data.get("total", 0.0)
        discretionary_goal = max(monthly_goal - fixed_expenses, 0)

        daily_average_total = monthly_expenses / days_elapsed if days_elapsed > 0 else 0
        daily_average_discr = discretionary_expenses / days_elapsed if days_elapsed > 0 else 0

        projected_total = daily_average_total * days_in_month
        projected_discr = daily_average_discr * days_in_month

        proportional_target = (discretionary_goal / days_in_month) * days_elapsed
        deviation = discretionary_expenses - proportional_target
        deviation_pct = (deviation / proportional_target * 100) if proportional_target > 0 else 0

        monthly_progress = {
            "days_in_month": days_in_month,
            "days_elapsed": days_elapsed,
            "days_remaining": days_in_month - days_elapsed,
            "progress_pct": round((days_elapsed / days_in_month) * 100, 1),
            "expenses_accumulated": round(monthly_expenses, 2),
            "fixed_expenses": round(fixed_expenses, 2),
            "fixed_items": fixed_items,
            "extraordinary_expenses": round(extraordinary_expenses_current, 2),
            "extraordinary_items": extraordinary_items_current,
            "discretionary_expenses": round(discretionary_expenses, 2),
            "daily_average": round(daily_average_discr, 2),
            "daily_average_total": round(daily_average_total, 2),
            "monthly_goal": monthly_goal,
            "discretionary_goal": round(discretionary_goal, 2),
            "projected_total": round(projected_total, 2),
            "projected_discr": round(projected_discr, 2),
            "proportional_target": round(proportional_target, 2),
            "deviation": round(deviation, 2),
            "deviation_pct": round(deviation_pct, 1),
            "goal_pct": round((discretionary_expenses / discretionary_goal) * 100, 1) if discretionary_goal > 0 else 0,
            "month_name": now.strftime("%B %Y"),
        }

        return jsonify({
            "success": True,
            "data": {
                "current_month": current_month,
                "previous_month": previous_month,
                "yesterday": yesterday,
                "weekly": weekly,
                "weekly_detail": weekly_detail,
                "extraordinary": extraordinary,
                "monthly_progress": monthly_progress,
                "last_updated": now.strftime("%Y-%m-%d %H:%M:%S"),
            },
        })
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(exc)}), 500


app.view_functions["panel_gastos_mes_detalle"] = panel_gastos_mes_detalle_patched
app.view_functions["panel_gastos_data"] = panel_gastos_data_patched


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
