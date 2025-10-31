import requests
from datetime import date, datetime, timedelta


def weather_banner(request):
    """
    Fetch current weather for Medellín from Open-Meteo (no API key) and
    expose minimal info for header banner. Fail silently on errors.
    """
    weather = None
    try:
        # Medellín approx coordinates
        resp = requests.get(
            'https://api.open-meteo.com/v1/forecast',
            params={
                'latitude': 6.2518,
                'longitude': -75.5636,
                'current_weather': True,
                'timezone': 'America/Bogota',
            },
            timeout=4
        )
        if resp.ok:
            data = resp.json()
            cw = data.get('current_weather') or {}
            if cw:
                weather = {
                    'temperature': cw.get('temperature'),
                    'windspeed': cw.get('windspeed'),
                }
    except Exception:
        weather = None
    return {'weather_current': weather}



_FX_CACHE: dict | None = None
_FX_CACHE_TTL = timedelta(minutes=10)


def _fetch_usd_cop_rate() -> dict | None:
    """Try primary provider (exchangerate.host), then fallback (open.er-api.com)."""
    # Primary: exchangerate.host (sin API key)
    try:
        resp = requests.get(
            "https://api.exchangerate.host/latest",
            params={"base": "USD", "symbols": "COP"},
            timeout=6,
        )
        if resp.ok:
            data = resp.json()
            # Some providers return {success:false, error:{...}}; guard against that
            rates = data.get("rates") or {}
            rate = rates.get("COP")
            if rate:
                return {
                    "base": "USD",
                    "quote": "COP",
                    "rate": round(float(rate), 2),
                    "date": data.get("date") or date.today().isoformat(),
                }
    except Exception:
        pass

    # Fallback: open.er-api.com (gratuito)
    try:
        resp = requests.get(
            "https://open.er-api.com/v6/latest/USD",
            timeout=6,
        )
        if resp.ok:
            data = resp.json()
            rates = data.get("rates") or {}
            rate = rates.get("COP")
            if rate:
                # open.er-api.com trae fecha como 'time_last_update_utc'
                date_str = data.get("time_last_update_utc") or date.today().isoformat()
                return {
                    "base": "USD",
                    "quote": "COP",
                    "rate": round(float(rate), 2),
                    "date": date_str,
                }
    except Exception:
        pass

    return None


def exchange_rate_banner(request):
    """
    Fetch USD->COP exchange rate and expose minimal info for the header banner.
    Uses in-memory cache and a fallback provider. Fail silently on errors.
    """
    global _FX_CACHE
    now = datetime.utcnow()
    
    # Check cache
    if _FX_CACHE is not None:
        cached_time = _FX_CACHE.get("fetched_at")
        if cached_time and (now - cached_time) < _FX_CACHE_TTL:
            return {"fx_rate": _FX_CACHE.get("value")}

    # Fetch new value
    value = _fetch_usd_cop_rate()
    _FX_CACHE = {"value": value, "fetched_at": now}
    return {"fx_rate": value}

