import hashlib
import httpx
from fastapi import HTTPException
from app.config import settings
from app.services.cache import get_cached, set_cached


def _safe_path(value: str) -> str:
    value = value.strip().strip("/")
    if not value or ".." in value or value.startswith("http:") or value.startswith("https:"):
        raise HTTPException(status_code=422, detail="Invalid CCKP query path")
    return value


async def climate_data(geocode: str | None = None, query_path: str | None = None) -> dict:
    if not settings.cckp_enabled:
        raise HTTPException(status_code=503, detail="World Bank CCKP integration is disabled in .env")
    geo = (geocode or settings.cckp_default_geocode).strip().upper()
    if not geo.replace(".", "").replace("_", "").isalnum():
        raise HTTPException(status_code=422, detail="Invalid geocode")
    path = _safe_path(query_path or settings.cckp_default_query_path)
    cache_key = "cckp_" + hashlib.sha256(f"{path}/{geo}".encode()).hexdigest()[:24]
    cached = get_cached(cache_key, ttl_seconds=24 * 3600)
    if cached:
        return cached
    url = f"{settings.cckp_api_base_url.rstrip('/')}/{path}/{geo}"
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout_seconds, follow_redirects=True) as client:
            response = await client.get(url, params={"_format": "json"})
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"World Bank CCKP request failed. Check the query path and geocode: {exc}") from exc
    result = {"source": "World Bank Climate Change Knowledge Portal", "source_url": url, "geocode": geo, "query_path": path, "data": payload, "interpretation_note": "Climate projection/climatology data are not a short-term weather forecast or a direct estimate of financial loss."}
    set_cached(cache_key, result)
    return result
