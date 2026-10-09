from typing import Any
from app.config import settings


def quantify_portfolio(holdings: list[dict[str, Any]], shock_pct: float | None = None) -> dict[str, Any]:
    """Scenario arithmetic only. Not a forecast, VaR model, or financial advice."""
    shock = settings.scenario_default_shock_pct if shock_pct is None else shock_pct
    if not 0 <= shock <= 100:
        raise ValueError("shock_pct must be between 0 and 100")
    total_value = sum(max(0.0, float(h.get("value") or 0)) for h in holdings)
    weight_sum = sum(max(0.0, float(h.get("weight") or 0)) for h in holdings)
    value_based = total_value > 0
    estimated_exposure = total_value if value_based else None
    loss = (total_value * shock / 100) if value_based else None
    # Weights are not automatically normalized; this flags the user's input rather than silently changing it.
    return {
        "method": "flat_shock_scenario",
        "scenario_shock_pct": shock,
        "holdings_count": len(holdings),
        "total_position_value": round(total_value, 2) if value_based else None,
        "scenario_loss_amount": round(loss, 2) if loss is not None else None,
        "portfolio_weight_total_pct": round(weight_sum, 4),
        "weights_sum_to_100": abs(weight_sum - 100.0) <= 0.5,
        "calculation_note": "Scenario loss = sum of provided market values × shock percentage. If values are absent, loss is not calculated. This is a user-selected sensitivity scenario, not a predicted loss or a climate attribution model.",
    }
