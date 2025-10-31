import requests


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


