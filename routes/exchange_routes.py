from flask import Blueprint, jsonify, request
from utils import token_required
from database import db, ExchangeRate
import requests
import time
from datetime import datetime, timedelta

exchange_bp = Blueprint('exchange', __name__, url_prefix='/api/exchange-rates')

DEFAULT_CURRENCIES = {
    "CZK": 1.0,
    "EUR": 0.041,
    "USD": 0.044,
    "GBP": 0.035
}

@exchange_bp.route('', methods=['GET'])
def get_exchange_rates():
    """Get currency exchange rates from DB or fetch live if expired"""
    
    # Check if we need to add a new tracking currency
    add_currency = request.args.get("add")
    if add_currency:
        add_currency = add_currency.upper()
        existing = ExchangeRate.query.filter_by(currency_code=add_currency).first()
        if not existing:
            # We don't have the rate yet, but we'll mark it for tracking
            new_rate = ExchangeRate(currency_code=add_currency, rate=1.0, is_tracked=True)
            db.session.add(new_rate)
            db.session.commit()
        elif not existing.is_tracked:
            existing.is_tracked = True
            db.session.commit()

    # Ensure defaults exist
    for c, default_rate in DEFAULT_CURRENCIES.items():
        if not ExchangeRate.query.filter_by(currency_code=c).first():
            db.session.add(ExchangeRate(currency_code=c, rate=default_rate, is_tracked=True))
    db.session.commit()

    # Check the newest update timestamp among tracked currencies
    tracked_rates = ExchangeRate.query.filter_by(is_tracked=True).all()
    if not tracked_rates:
        return jsonify({"rates": {}}), 200

    # Find the oldest last_updated among tracked rates. Wait, just checking if ANY needs an update.
    # It's better to check if it's been > 1 hour since we last fetched.
    # Because last_updated might be None or old if the server was restarted or just added.
    needs_update = False
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)
    
    for rate_obj in tracked_rates:
        if not rate_obj.last_updated or rate_obj.last_updated < one_hour_ago:
            needs_update = True
            break
            
    if needs_update:
        try:
            response = requests.get("https://api.exchangerate-api.com/v4/latest/CZK", timeout=5)
            response.raise_for_status()
            data = response.json()
            api_rates = data.get("rates", {})
            api_rates["CZK"] = 1.0 # Ensure base is present
            
            for rate_obj in tracked_rates:
                code = rate_obj.currency_code
                if code in api_rates:
                    rate_obj.rate = api_rates[code]
                    rate_obj.last_updated = now
            db.session.commit()
            
            # Re-fetch tracked after update
            tracked_rates = ExchangeRate.query.filter_by(is_tracked=True).all()
            
        except Exception as e:
            print(f"Error fetching live exchange rates: {e}")
            # we'll just fall through and return whatever we have in DB
            pass

    # Build the response dict
    retval = {}
    newest_update = None
    for r in tracked_rates:
        if r.rate:
            retval[r.currency_code] = r.rate
            if r.last_updated:
                if not newest_update or r.last_updated > newest_update:
                    newest_update = r.last_updated
            
    response_data = {"rates": retval}
    if newest_update:
        response_data["last_updated"] = newest_update.isoformat()
        
    return jsonify(response_data), 200
