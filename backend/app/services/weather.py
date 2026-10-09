import httpx
from fastapi import HTTPException
from app.config import settings
from app.services.cache import get_cached, set_cached


async def forecast(latitude: float, longitude: float, forecast_days: int | None = None) -> dict:
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise HTTPException(status_code=422, detail="Latitude must be -90..90 and longitude -180..180")
    days = max(1, min(forecast_days or settings.open_meteo_forecast_days, 16))
    cache_key = f"weather_{latitude:.3f}_{longitude:.3f}_{days}".replace("-", "m").replace(".", "p")
    cached = get_cached(cache_key, ttl_seconds=min(settings.cache_ttl_seconds, 900))
    if cached:
        return cached
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": settings.open_meteo_hourly,
        "daily": settings.open_meteo_daily,
        "forecast_days": days,
        "timezone": "auto",
    }
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
            response = await client.get(settings.open_meteo_base_url, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Open-Meteo request failed: {exc}") from exc
    result = {"source": "Open-Meteo", "source_url": settings.open_meteo_base_url, "fetched_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(), "data": payload}
    set_cached(cache_key, result)
    return result
