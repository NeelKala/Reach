import json
import time
from pathlib import Path
from typing import Any
from app.config import settings


def _cache_dir() -> Path:
    p = settings.data_path / "cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_cached(key: str, ttl_seconds: int | None = None) -> Any | None:
    path = _cache_dir() / f"{key}.json"
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        ttl = settings.cache_ttl_seconds if ttl_seconds is None else ttl_seconds
        if time.time() - float(obj.get("cached_at", 0)) > ttl:
            return None
        return obj.get("payload")
    except (OSError, ValueError, TypeError):
        return None


def set_cached(key: str, payload: Any) -> None:
    path = _cache_dir() / f"{key}.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps({"cached_at": time.time(), "payload": payload}, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)
