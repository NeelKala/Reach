from app.services.risk import quantify_portfolio


def test_flat_shock_scenario():
    result = quantify_portfolio([{"value": 1000, "weight": 60}, {"value": 500, "weight": 40}], 10)
    assert result["total_position_value"] == 1500
    assert result["scenario_loss_amount"] == 150
    assert result["weights_sum_to_100"] is True


def test_no_values_does_not_invent_loss():
    result = quantify_portfolio([{"company": "Example", "weight": 100}], 5)
    assert result["scenario_loss_amount"] is None
    assert result["total_position_value"] is None
