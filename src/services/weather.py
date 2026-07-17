"""Free, keyless daily weather for the shop — Open-Meteo.

Angel, on the My Day timesheet: "the weather report should be automated based on the shop's address, not
typed in. There must be a free, very accurate weather API with no account. When it's a rainy day and only
two sales, she shouldn't have to fake it — it comes from a REAL source, not something she makes up."

Open-Meteo (open-meteo.com) is exactly that: no API key, no account, no rate-limit ceremony — free for
non-commercial use, accurate, and it publishes its own free geocoding (address → lat/lon). So: the shop's
city → coordinates → today's weather → one clean line the timesheet fills in for the operator.

Never raises. Weather is a nicety on a note; if the lookup fails the note is simply weather-less.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_GEO_CACHE: dict[str, tuple[float, float]] = {}   # (city|country) -> (lat, lon); geocode once per run

# WMO weather codes (the Open-Meteo `weather_code`) → an emoji + plain label. Grouped as a shop cares.
_WMO = {
    0: ("☀️", "Clear"),
    1: ("🌤️", "Mostly clear"), 2: ("⛅", "Partly cloudy"), 3: ("☁️", "Overcast"),
    45: ("🌫️", "Fog"), 48: ("🌫️", "Fog"),
    51: ("🌦️", "Light drizzle"), 53: ("🌦️", "Drizzle"), 55: ("🌦️", "Heavy drizzle"),
    56: ("🌧️", "Freezing drizzle"), 57: ("🌧️", "Freezing drizzle"),
    61: ("🌧️", "Light rain"), 63: ("🌧️", "Rain"), 65: ("🌧️", "Heavy rain"),
    66: ("🌧️", "Freezing rain"), 67: ("🌧️", "Freezing rain"),
    71: ("🌨️", "Light snow"), 73: ("🌨️", "Snow"), 75: ("❄️", "Heavy snow"), 77: ("🌨️", "Snow grains"),
    80: ("🌦️", "Rain showers"), 81: ("🌧️", "Rain showers"), 82: ("⛈️", "Violent rain showers"),
    85: ("🌨️", "Snow showers"), 86: ("❄️", "Heavy snow showers"),
    95: ("⛈️", "Thunderstorm"), 96: ("⛈️", "Thunderstorm + hail"), 99: ("⛈️", "Thunderstorm + hail"),
}


async def _geocode(client, city: str, country: str = "") -> tuple[float, float] | None:
    key = f"{city.strip().lower()}|{country.strip().lower()}"
    if key in _GEO_CACHE:
        return _GEO_CACHE[key]
    params = {"name": city.strip(), "count": 1, "language": "en", "format": "json"}
    if country.strip():
        params["country"] = country.strip()
    r = await client.get("https://geocoding-api.open-meteo.com/v1/search", params=params)
    if r.status_code != 200:
        return None
    res = (r.json() or {}).get("results") or []
    if not res:
        return None
    lat, lon = float(res[0]["latitude"]), float(res[0]["longitude"])
    _GEO_CACHE[key] = (lat, lon)
    return (lat, lon)


async def daily_weather_line(city: str, country: str = "",
                             lat: float | None = None, lon: float | None = None) -> str:
    """A one-liner for today at the shop, e.g. "⛈️ Thunderstorm, 18–30 °C" — or "" if we can't tell.

    Pass lat/lon to skip geocoding (a shop can cache its coords); otherwise the city is geocoded (once
    per process). Uses today's forecast: the daily code + the min/max, since a shift spans the day, not
    the instant.
    """
    if not (city or "").strip() and lat is None:
        return ""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            if lat is None or lon is None:
                geo = await _geocode(client, city, country)
                if not geo:
                    return ""
                lat, lon = geo
            r = await client.get("https://api.open-meteo.com/v1/forecast", params={
                "latitude": lat, "longitude": lon,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                "timezone": "auto", "forecast_days": 1,
            })
        if r.status_code != 200:
            return ""
        d = (r.json() or {}).get("daily") or {}
        code = (d.get("weather_code") or [None])[0]
        tmax = (d.get("temperature_2m_max") or [None])[0]
        tmin = (d.get("temperature_2m_min") or [None])[0]
        if code is None:
            return ""
        emoji, label = _WMO.get(int(code), ("🌡️", "Mixed"))
        if tmin is not None and tmax is not None:
            lo, hi = round(tmin), round(tmax)
            temp = f"{lo}–{hi} °C" if lo != hi else f"{hi} °C"
            return f"{emoji} {label}, {temp}"
        return f"{emoji} {label}"
    except Exception as e:
        logger.info(f"weather lookup failed for {city!r}: {str(e)[:60]}")
        return ""
