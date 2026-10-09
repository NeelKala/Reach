import httpx
from fastapi import HTTPException
from app.config import settings


async def call_quantify(payload: dict) -> dict:
    if not settings.quantify_enabled:
        raise HTTPException(status_code=503, detail="Quantify connector is not configured. Set QUANTIFY_ENABLED=true and add the provider's documented endpoint and key in .env")
    if not settings.quantify_api_base_url.strip():
        raise HTTPException(status_code=503, detail="QUANTIFY_API_BASE_URL is missing in .env")
    url = settings.quantify_api_base_url.rstrip("/") + "/" + settings.quantify_api_path.strip("/")
    headers = {"Content-Type": "application/json"}
    if settings.quantify_api_key:
        prefix = settings.quantify_api_key_prefix.strip()
        headers[settings.quantify_api_key_header] = f"{prefix} {settings.quantify_api_key}".strip()
    try:
        async with httpx.AsyncClient(timeout=settings.quantify_timeout_seconds) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return {"provider": "Quantify", "configured": True, "data": response.json()}
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Quantify provider returned HTTP {exc.response.status_code}") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Quantify provider request failed: {exc}") from exc
