
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Reach API"
    app_version: str = "1.0.0"
    environment: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    data_dir: str = "data"
    http_timeout_seconds: float = 20.0
    cache_ttl_seconds: int = 1800
    max_upload_mb: int = 10

    # Zerodha Kite Connect credentials.
    # Configure these in backend/.env; never expose them to the frontend.
    kite_api_key: str = ""
    kite_access_token: str = ""

    sectivia_dataset_url: str = (
        "https://sectivia.com/dataset/sectivia-supply-chain.json"
    )
    sectivia_companies_csv_url: str = (
        "https://sectivia.com/dataset/sectivia-companies.csv"
    )
    sectivia_relations_csv_url: str = (
        "https://sectivia.com/dataset/sectivia-relations.csv"
    )
    sectivia_local_json_path: str = (
        "data/sectivia/sectivia-supply-chain.json"
    )
    sectivia_auto_refresh: bool = True

    open_meteo_base_url: str = (
        "https://api.open-meteo.com/v1/forecast"
    )
    open_meteo_archive_url: str = (
        "https://archive-api.open-meteo.com/v1/archive"
    )
    open_meteo_hourly: str = (
        "temperature_2m,relative_humidity_2m,precipitation,"
        "precipitation_probability,wind_speed_10m,wind_gusts_10m"
    )
    open_meteo_daily: str = (
        "temperature_2m_max,temperature_2m_min,precipitation_sum,"
        "precipitation_probability_max,wind_speed_10m_max"
    )
    open_meteo_forecast_days: int = 7

    cckp_api_base_url: str = (
        "https://cckpapi.worldbank.org/cckp/v1"
    )
    cckp_default_query_path: str = (
        "cmip6-x0.25_climatology_tas,tasmin,tasmax_climatology_"
        "annual_1995-2014_median_historical_ensemble_all_mean"
    )
    cckp_default_geocode: str = "IND"
    cckp_enabled: bool = True

    quantify_enabled: bool = False
    quantify_api_base_url: str = ""
    quantify_api_path: str = "/"
    quantify_api_key: str = ""
    quantify_api_key_header: str = "Authorization"
    quantify_api_key_prefix: str = "Bearer"
    quantify_timeout_seconds: float = 15.0

    scenario_default_shock_pct: float = 5.0
    scenario_severe_shock_pct: float = 15.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def project_root(self) -> Path:
        # Running from backend/ is the supported workflow.
        # This also works if launched from its parent.
        return Path(__file__).resolve().parents[1]

    @property
    def data_path(self) -> Path:
        path = Path(self.data_dir)
        return (
            path
            if path.is_absolute()
            else self.project_root / path
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
