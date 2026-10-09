import csv
import io
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import HTTPException, UploadFile
from app.config import settings

ALIASES = {
    "company": ("company", "company_name", "name", "issuer", "holding"),
    "ticker": ("ticker", "symbol", "stock_symbol", "company_ticker"),
    "sector": ("sector", "industry", "gics_sector"),
    "weight": ("weight", "portfolio_weight", "allocation", "weight_pct", "percentage"),
    "region": ("region", "country", "geography", "market"),
    "value": ("value", "market_value", "position_value", "amount", "holding_value"),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lon", "lng"),
}


def _first(row: dict, names: tuple[str, ...], default=None):
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for name in names:
        value = lowered.get(name)
        if value not in (None, ""):
            return value
    return default


def _number(value, default=0.0):
    try:
        return float(str(value).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return default


def normalise_holding(row: dict, index: int) -> dict[str, Any]:
    return {
        "id": str(row.get("id") or f"holding-{index+1}"),
        "company": str(_first(row, ALIASES["company"], f"Company {index+1}")),
        "ticker": str(_first(row, ALIASES["ticker"], "")).upper().strip(),
        "sector": str(_first(row, ALIASES["sector"], "Unspecified")),
        "weight": _number(_first(row, ALIASES["weight"], 0)),
        "region": str(_first(row, ALIASES["region"], "Unspecified")),
        "value": _number(_first(row, ALIASES["value"], 0)),
        "latitude": _optional_number(_first(row, ALIASES["latitude"])),
        "longitude": _optional_number(_first(row, ALIASES["longitude"])),
        "source_fields": row,
    }


def _optional_number(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_csv(text: str) -> list[dict]:
    return [normalise_holding(row, i) for i, row in enumerate(csv.DictReader(io.StringIO(text-sig(text))))]


def sig(text: str) -> str:
    return text.lstrip("\ufeff")


def parse_json(text: str) -> list[dict]:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc.msg}") from exc
    if isinstance(raw, dict):
        raw = raw.get("holdings", raw.get("companies", raw.get("data", [raw])))
    if not isinstance(raw, list):
        raise HTTPException(status_code=400, detail="JSON must be a list or an object containing holdings/companies/data")
    return [normalise_holding(row, i) for i, row in enumerate(raw) if isinstance(row, dict)]


async def parse_upload(file: UploadFile) -> tuple[str, list[dict]]:
    name = file.filename or "portfolio.csv"
    ext = Path(name).suffix.lower()
    if ext not in {".csv", ".json"}:
        raise HTTPException(status_code=415, detail="Upload a .csv or .json portfolio file")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB limit")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded") from exc
    holdings = parse_csv(text) if ext == ".csv" else parse_json(text)
    if not holdings:
        raise HTTPException(status_code=400, detail="No holdings found. Check the file headers and rows")
    if len(holdings) > 10000:
        raise HTTPException(status_code=413, detail="Portfolio has more than 10,000 rows")
    return name, holdings


def save_portfolio(name: str, holdings: list[dict]) -> dict:
    folder = settings.data_path / "portfolios"
    folder.mkdir(parents=True, exist_ok=True)
    portfolio_id = uuid.uuid4().hex[:12]
    record = {"id": portfolio_id, "name": name, "created_at": datetime.now(timezone.utc).isoformat(), "holdings": holdings}
    (folder / f"{portfolio_id}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def list_portfolios() -> list[dict]:
    folder = settings.data_path / "portfolios"
    folder.mkdir(parents=True, exist_ok=True)
    result = []
    for path in sorted(folder.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            result.append({"id": item["id"], "name": item["name"], "created_at": item.get("created_at"), "holdings_count": len(item.get("holdings", []))})
        except (OSError, ValueError, KeyError):
            continue
    return result


def get_portfolio(portfolio_id: str) -> dict:
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", portfolio_id):
        raise HTTPException(status_code=400, detail="Invalid portfolio id")
    path = settings.data_path / "portfolios" / f"{portfolio_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Portfolio not found")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=500, detail="Could not read stored portfolio") from exc
