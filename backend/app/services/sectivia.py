import csv
import io
import json
from pathlib import Path
from typing import Any
import httpx
from app.config import settings
from app.services.cache import get_cached, set_cached


def _first(obj: dict, *keys: str, default=None):
    for key in keys:
        if key in obj and obj[key] not in (None, ""):
            return obj[key]
    return default


def _records_from_csv(text: str) -> list[dict[str, Any]]:
    return [dict(row) for row in csv.DictReader(io.StringIO(text))]


def _normalise_dataset(raw: Any) -> dict[str, Any]:
    """Normalize Sectivia JSON without discarding source fields or assuming every field exists."""
    if isinstance(raw, list):
        raw = {"records": raw}
    if not isinstance(raw, dict):
        raise ValueError("Sectivia JSON root must be an object or list")

    companies_raw = _first(raw, "companies", "nodes", "company", default=[])
    relations_raw = _first(raw, "relations", "edges", "relationships", "links", default=[])
    if isinstance(companies_raw, dict):
        companies_raw = list(companies_raw.values())
    if isinstance(relations_raw, dict):
        relations_raw = list(relations_raw.values())
    if not isinstance(companies_raw, list):
        companies_raw = []
    if not isinstance(relations_raw, list):
        relations_raw = []

    companies = []
    by_ticker: dict[str, dict] = {}
    for i, item in enumerate(companies_raw):
        if not isinstance(item, dict):
            continue
        ticker = str(_first(item, "ticker", "symbol", "companyTicker", "id", default=f"UNKNOWN-{i}")).strip()
        company = {
            **item,
            "ticker": ticker,
            "name": _first(item, "name", "company", "companyName", "company_name", default=ticker),
            "sector": _first(item, "sector", "industry", default=None),
            "listed": _first(item, "listed", default=None),
        }
        companies.append(company)
        by_ticker[ticker.upper()] = company

    relations = []
    for i, item in enumerate(relations_raw):
        if not isinstance(item, dict):
            continue
        customer = _first(item, "customerTicker", "customer_ticker", "customer", "buyer", "from", "source")
        supplier = _first(item, "supplierTicker", "supplier_ticker", "supplier", "seller", "to", "target")
        # Sectivia relation files may contain cross-sector records; preserve them even if one endpoint is a sector label.
        if customer is None and supplier is None:
            continue
        relations.append({
            **item,
            "id": str(_first(item, "id", "relationId", default=f"relation-{i+1}")),
            "customerTicker": str(customer) if customer is not None else None,
            "supplierTicker": str(supplier) if supplier is not None else None,
            "what": _first(item, "what", "description", "product", "relationship", default=None),
            "cross": bool(item.get("cross", False)),
            "customer": by_ticker.get(str(customer).upper()) if customer is not None else None,
            "supplier": by_ticker.get(str(supplier).upper()) if supplier is not None else None,
        })
    return {
        "source": "Sectivia supply-chain dataset",
        "source_url": settings.sectivia_dataset_url,
        "companies": companies,
        "relations": relations,
        "counts": {"companies": len(companies), "relations": len(relations)},
    }


async def load_dataset(force_refresh: bool = False) -> dict[str, Any]:
    local = Path(settings.sectivia_local_json_path)
    if not local.is_absolute():
        local = settings.project_root / local
    if local.exists() and not force_refresh:
        try:
            return _normalise_dataset(json.loads(local.read_text(encoding="utf-8")))
        except (OSError, ValueError, json.JSONDecodeError):
            pass

    cached = None if force_refresh else get_cached("sectivia_dataset", ttl_seconds=settings.cache_ttl_seconds)
    if cached:
        return cached

    if not settings.sectivia_auto_refresh and local.exists():
        return _normalise_dataset(json.loads(local.read_text(encoding="utf-8")))

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds, follow_redirects=True) as client:
        response = await client.get(settings.sectivia_dataset_url)
        response.raise_for_status()
        raw = response.json()
    data = _normalise_dataset(raw)
    set_cached("sectivia_dataset", data)
    # Save the unmodified upstream JSON as an inspectable local snapshot.
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


async def load_csv_fallback() -> dict[str, Any]:
    """Fallback for the dataset's published CSV files if the JSON endpoint is unavailable."""
    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds, follow_redirects=True) as client:
        companies_response, relations_response = await client.get(settings.sectivia_companies_csv_url), await client.get(settings.sectivia_relations_csv_url)
        companies_response.raise_for_status()
        relations_response.raise_for_status()
    return _normalise_dataset({"companies": _records_from_csv(companies_response.text), "relations": _records_from_csv(relations_response.text)})


def find_company(dataset: dict, ticker: str) -> dict | None:
    target = ticker.strip().upper()
    for company in dataset["companies"]:
        if str(company.get("ticker", "")).upper() == target:
            return company
    return None


def company_neighborhood(dataset: dict, ticker: str, depth: int = 1) -> dict[str, Any]:
    target = ticker.strip().upper()
    company = find_company(dataset, target)
    if not company:
        return {"ticker": target, "nodes": [], "edges": [], "found": False}
    seen = {target}
    frontier = {target}
    selected_edges = []
    for _ in range(max(1, min(depth, 3))):
        next_frontier = set()
        for edge in dataset["relations"]:
            a = str(edge.get("customerTicker") or "").upper()
            b = str(edge.get("supplierTicker") or "").upper()
            if a in frontier or b in frontier:
                selected_edges.append(edge)
                if a and a not in seen:
                    next_frontier.add(a)
                if b and b not in seen:
                    next_frontier.add(b)
        frontier = next_frontier - seen
        seen.update(frontier)
        if not frontier:
            break
    companies = {str(c.get("ticker", "")).upper(): c for c in dataset["companies"]}
    nodes = [companies[t] for t in seen if t in companies]
    return {"ticker": target, "found": True, "nodes": nodes, "edges": selected_edges, "depth": depth}
