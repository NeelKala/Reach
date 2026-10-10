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


# Header aliases are normalized before matching, so spaces, underscores,
# capitalization, and punctuation differences are handled consistently.
ALIASES = {
    "company": (
        "company",
        "company_name",
        "name",
        "issuer",
        "holding",
        "company_or_issuer",
    ),
    "ticker": (
        "ticker",
        "symbol",
        "stock_symbol",
        "company_ticker",
    ),
    "sector": (
        "sector",
        "industry",
        "gics_sector",
    ),
    "weight": (
        "weight",
        "portfolio_weight",
        "allocation",
        "weight_pct",
        "weight_percent",
        "portfolio_weight_pct",
        "portfolio_weight_percent",
        "portfolio_weight_percentage",
        "weight_percentage",
        "weight_percent_of_portfolio",
        "percentage",
        "allocation_pct",
        "allocation_percent",
    ),
    "region": (
        "region",
        "country",
        "geography",
        "market",
        "country_or_region",
        "country_region",
    ),
    "value": (
        "value",
        "market_value",
        "position_value",
        "amount",
        "holding_value",
        "market_value_usd",
        "market_value_in_usd",
        "position_market_value",
        "investment_value",
    ),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lon", "lng", "long"),
}


def _normalise_key(key: Any) -> str:
    """Normalize a field name for reliable alias matching."""
    key = str(key).strip().lstrip("\ufeff").lower()
    return re.sub(r"[^a-z0-9]+", "_", key).strip("_")


# Pre-normalize the alias table once.
NORMALIZED_ALIASES = {
    field: tuple(_normalise_key(alias) for alias in aliases)
    for field, aliases in ALIASES.items()
}


def _normalized_row(row: dict) -> dict:
    """Normalize headers while retaining their associated values."""
    return {
        _normalise_key(key): value
        for key, value in row.items()
        if key is not None
    }


def _first(row: dict, names: tuple[str, ...], default=None):
    lowered = _normalized_row(row)

    for name in names:
        key = _normalise_key(name)
        value = lowered.get(key)

        if value is not None and str(value).strip() != "":
            return value

    return default


def _number(value, default=0.0) -> float:
    """
    Parse numeric values such as:
      12.5
      "12.5%"
      "$1,250.00"
      "(1,250.00)"

    Missing or invalid values use the supplied default.
    """
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return float(value) if value == value else default

    text = str(value).strip()

    if not text:
        return default

    negative = text.startswith("(") and text.endswith(")")
    if negative:
        text = text[1:-1].strip()

    text = (
        text.replace(",", "")
        .replace("$", "")
        .replace("₹", "")
        .replace("€", "")
        .replace("£", "")
        .replace("%", "")
        .strip()
    )

    try:
        result = float(text)
        if result != result or result in (float("inf"), float("-inf")):
            return default
        return -result if negative else result
    except (TypeError, ValueError):
        return default


def _optional_number(value):
    """Return None for absent or invalid optional coordinates."""
    if value is None or str(value).strip() == "":
        return None

    parsed = _number(value, default=None)
    return parsed


def normalise_holding(row: dict, index: int) -> dict[str, Any]:
    """
    Convert a source CSV/JSON row into the standard holding schema.

    Original source fields are retained in source_fields for traceability.
    """
    company = _first(
        row,
        NORMALIZED_ALIASES["company"],
        _first(row, NORMALIZED_ALIASES["ticker"], f"Company {index + 1}"),
    )

    ticker = _first(row, NORMALIZED_ALIASES["ticker"], "")
    sector = _first(row, NORMALIZED_ALIASES["sector"], "Unspecified")
    weight = _first(row, NORMALIZED_ALIASES["weight"], 0)
    region = _first(row, NORMALIZED_ALIASES["region"], "Unspecified")
    value = _first(row, NORMALIZED_ALIASES["value"], 0)

    return {
        "id": str(row.get("id") or f"holding-{index + 1}"),
        "company": str(company).strip(),
        "ticker": str(ticker).upper().strip(),
        "sector": str(sector).strip() or "Unspecified",
        "weight": _number(weight),
        "region": str(region).strip() or "Unspecified",
        "value": _number(value),
        "latitude": _optional_number(
            _first(row, NORMALIZED_ALIASES["latitude"])
        ),
        "longitude": _optional_number(
            _first(row, NORMALIZED_ALIASES["longitude"])
        ),
        "source_fields": row,
    }


def sig(text: str) -> str:
    """Remove a UTF-8 byte-order mark if present."""
    return text.lstrip("\ufeff")


def parse_csv(text: str) -> list[dict]:
    """Parse CSV content into normalized portfolio holdings."""
    cleaned_text = sig(text)
    reader = csv.DictReader(io.StringIO(cleaned_text))

    if not reader.fieldnames:
        return []

    # Reject completely blank records but preserve legitimate zero values.
    holdings = []

    for index, row in enumerate(reader):
        if not row or not any(
            value is not None and str(value).strip()
            for value in row.values()
        ):
            continue

        holdings.append(normalise_holding(row, len(holdings)))

    return holdings


def parse_json(text: str) -> list[dict]:
    """Parse a JSON list or supported portfolio object."""
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON: {exc.msg}",
        ) from exc

    if isinstance(raw, dict):
        raw = raw.get(
            "holdings",
            raw.get("companies", raw.get("data", [raw])),
        )

    if not isinstance(raw, list):
        raise HTTPException(
            status_code=400,
            detail=(
                "JSON must be a list or an object containing "
                "holdings/companies/data"
            ),
        )

    holdings = []

    for row in raw:
        if isinstance(row, dict):
            holdings.append(normalise_holding(row, len(holdings)))

    return holdings


async def parse_upload(file: UploadFile) -> tuple[str, list[dict]]:
    """Validate and parse an uploaded CSV or JSON portfolio."""
    name = file.filename or "portfolio.csv"
    ext = Path(name).suffix.lower()

    if ext not in {".csv", ".json"}:
        raise HTTPException(
            status_code=415,
            detail="Upload a .csv or .json portfolio file",
        )

    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = await file.read(max_bytes + 1)

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_upload_mb} MB limit",
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail="File must be UTF-8 encoded",
        ) from exc

    holdings = parse_csv(text) if ext == ".csv" else parse_json(text)

    if not holdings:
        raise HTTPException(
            status_code=400,
            detail="No holdings found. Check the file headers and rows",
        )

    if len(holdings) > 10000:
        raise HTTPException(
            status_code=413,
            detail="Portfolio has more than 10,000 rows",
        )

    return name, holdings


def save_portfolio(name: str, holdings: list[dict]) -> dict:
    """Persist a portfolio as a JSON file."""
    folder = settings.data_path / "portfolios"
    folder.mkdir(parents=True, exist_ok=True)

    portfolio_id = uuid.uuid4().hex[:12]

    record = {
        "id": portfolio_id,
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "holdings": holdings,
    }

    output_path = folder / f"{portfolio_id}.json"
    output_path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return record


def list_portfolios() -> list[dict]:
    """Return portfolio metadata for the saved-portfolio selector."""
    folder = settings.data_path / "portfolios"
    folder.mkdir(parents=True, exist_ok=True)

    result = []

    for path in sorted(
        folder.glob("*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))

            result.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "created_at": item.get("created_at"),
                    "holdings_count": len(item.get("holdings", [])),
                }
            )
        except (OSError, ValueError, KeyError):
            continue

    return result


def get_portfolio(portfolio_id: str) -> dict:
    """Retrieve a saved portfolio by its validated identifier."""
    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,80}", portfolio_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid portfolio id",
        )

    path = settings.data_path / "portfolios" / f"{portfolio_id}.json"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Portfolio not found",
        )

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not read stored portfolio",
        ) from exc
