from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any
from fastapi import FastAPI, File, Query, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from app.config import settings
from app.services import sectivia, weather, climate, portfolio, risk, quantify


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.data_path.mkdir(parents=True, exist_ok=True)
    (settings.data_path / "cache").mkdir(parents=True, exist_ok=True)
    (settings.data_path / "portfolios").mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, description="Reach climate and supply-chain risk intelligence API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


class ScenarioRequest(BaseModel):
    holdings: list[dict[str, Any]] = Field(min_length=1, max_length=10000)
    shock_pct: float | None = Field(default=None, ge=0, le=100)


class QuantifyRequest(BaseModel):
    holdings: list[dict[str, Any]] = Field(min_length=1, max_length=10000)
    context: dict[str, Any] = Field(default_factory=dict)


@app.get("/")
def root():
    return {"service": settings.app_name, "version": settings.app_version, "status": "running", "docs": "/docs"}


@app.get(f"{settings.api_prefix}/health")
def health():
    return {"status": "healthy", "service": settings.app_name, "timestamp": datetime.now(timezone.utc).isoformat(), "providers": {"sectivia": "configured", "open_meteo": "configured", "world_bank_cckp": "enabled" if settings.cckp_enabled else "disabled", "quantify": "enabled" if settings.quantify_enabled else "not_configured"}}


@app.get(f"{settings.api_prefix}/config/public")
def public_config():
    """Only non-secret client configuration; never returns keys or credentials."""
    return {"api_prefix": settings.api_prefix, "sources": {"sectivia": settings.sectivia_dataset_url, "open_meteo": settings.open_meteo_base_url, "world_bank_cckp": settings.cckp_api_base_url}, "quantify_enabled": settings.quantify_enabled}


@app.get(f"{settings.api_prefix}/data/sources")
def data_sources():
    return {"sources": [
        {"id": "sectivia", "name": "Sectivia supply-chain dataset", "mode": "remote JSON with local snapshot and cache", "url": settings.sectivia_dataset_url, "authentication_required": False},
        {"id": "world_bank_cckp", "name": "World Bank Climate Change Knowledge Portal", "mode": "live API with 24-hour cache", "url": settings.cckp_api_base_url, "authentication_required": False},
        {"id": "open_meteo", "name": "Open-Meteo", "mode": "live forecast API with short cache", "url": settings.open_meteo_base_url, "authentication_required": False},
    ]}


@app.get(f"{settings.api_prefix}/supply-chain/summary")
async def supply_chain_summary(refresh: bool = False):
    try:
        data = await sectivia.load_dataset(force_refresh=refresh)
    except Exception as exc:
        try:
            data = await sectivia.load_csv_fallback()
        except Exception as fallback_exc:
            raise HTTPException(status_code=502, detail=f"Could not load Sectivia dataset or CSV fallback: {fallback_exc}") from exc
    return {"source": data["source"], "source_url": data["source_url"], "counts": data["counts"], "sample_companies": data["companies"][:8], "sample_relations": data["relations"][:8], "loaded_at": datetime.now(timezone.utc).isoformat()}


@app.get(f"{settings.api_prefix}/supply-chain/companies")
async def search_companies(q: str = "", sector: str | None = None, limit: int = Query(default=50, ge=1, le=500)):
    try:
        data = await sectivia.load_dataset()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load Sectivia dataset: {exc}") from exc
    query = q.casefold().strip()
    rows = data["companies"]
    if query:
        rows = [c for c in rows if query in str(c.get("name", "")).casefold() or query in str(c.get("ticker", "")).casefold() or query in str(c.get("sector", "")).casefold()]
    if sector:
        rows = [c for c in rows if str(c.get("sector", "")).casefold() == sector.casefold()]
    return {"count": len(rows), "items": rows[:limit], "source": data["source"]}


@app.get(f"{settings.api_prefix}/supply-chain/companies/{{ticker}}")
async def company_detail(ticker: str):
    try:
        data = await sectivia.load_dataset()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load Sectivia dataset: {exc}") from exc
    company = sectivia.find_company(data, ticker)
    if not company:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found in Sectivia dataset")
    network = sectivia.company_neighborhood(data, ticker, depth=1)
    return {"company": company, "relationships": network["edges"], "connected_companies": network["nodes"], "source": data["source"]}


@app.get(f"{settings.api_prefix}/supply-chain/graph/{{ticker}}")
async def company_graph(ticker: str, depth: int = Query(default=2, ge=1, le=3)):
    try:
        data = await sectivia.load_dataset()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load Sectivia dataset: {exc}") from exc
    result = sectivia.company_neighborhood(data, ticker, depth=depth)
    if not result["found"]:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found in Sectivia dataset")
    return {**result, "source": data["source"], "note": "Edges represent recorded supplier/customer relationships. Missing relationships do not imply no real-world dependency."}


@app.get(f"{settings.api_prefix}/weather/forecast")
async def weather_forecast(latitude: float = Query(..., ge=-90, le=90), longitude: float = Query(..., ge=-180, le=180), days: int = Query(default=7, ge=1, le=16)):
    return await weather.forecast(latitude, longitude, days)


@app.get(f"{settings.api_prefix}/climate/cckp")
async def world_bank_climate(geocode: str | None = None, query_path: str | None = None):
    return await climate.climate_data(geocode=geocode, query_path=query_path)


@app.post(f"{settings.api_prefix}/portfolios/upload")
async def upload_portfolio(file: UploadFile = File(...)):
    name, holdings = await portfolio.parse_upload(file)
    record = portfolio.save_portfolio(name, holdings)
    return {"id": record["id"], "name": record["name"], "created_at": record["created_at"], "holdings_count": len(holdings), "holdings": holdings, "quantification": risk.quantify_portfolio(holdings)}


@app.get(f"{settings.api_prefix}/portfolios")
def list_saved_portfolios():
    return {"count": len(portfolio.list_portfolios()), "items": portfolio.list_portfolios()}


@app.get(f"{settings.api_prefix}/portfolios/{{portfolio_id}}")
def get_saved_portfolio(portfolio_id: str):
    record = portfolio.get_portfolio(portfolio_id)
    record["quantification"] = risk.quantify_portfolio(record.get("holdings", []))
    return record


@app.post(f"{settings.api_prefix}/risk/quantify")
def quantify_risk(request: ScenarioRequest):
    return risk.quantify_portfolio(request.holdings, request.shock_pct)


@app.post(f"{settings.api_prefix}/quantify/provider")
async def quantify_provider(request: QuantifyRequest):
    return await quantify.call_quantify({"holdings": request.holdings, "context": request.context})


@app.get(f"{settings.api_prefix}/search")
async def global_search(q: str = Query(..., min_length=1, max_length=120), limit: int = Query(default=10, ge=1, le=50)):
    try:
        data = await sectivia.load_dataset()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load Sectivia dataset: {exc}") from exc
    term = q.casefold().strip()
    companies = [c for c in data["companies"] if term in str(c.get("name", "")).casefold() or term in str(c.get("ticker", "")).casefold() or term in str(c.get("sector", "")).casefold()][:limit]
    return {"query": q, "companies": companies, "count": len(companies), "source": data["source"]}
