from __future__ import annotations

import pytest

from energy_optimizer.assets import (
    AssetDispatchRequest,
    BatterySpec,
    simulate_asset_dispatch,
)


def test_pv_surplus_charges_battery_before_export() -> None:
    request = AssetDispatchRequest(
        base_load_kw=(2.0,),
        pv_generation_kw=(5.0,),
        prices_per_kwh=(1.0,),
        slot_hours=1.0,
        battery=BatterySpec(
            capacity_kwh=4.0, max_charge_kw=2.0, max_discharge_kw=2.0,
            initial_soc_kwh=0.0,
        ),
    )
    result = simulate_asset_dispatch(request)
    row = result.slots[0]
    assert row.pv_used_kw == pytest.approx(2.0)
    assert row.battery_charge_kw == pytest.approx(2.0)
    assert row.pv_export_kw == pytest.approx(1.0)
    assert row.state_of_charge_kwh == pytest.approx(1.9)


def test_battery_discharge_reduces_peak_import() -> None:
    request = AssetDispatchRequest(
        base_load_kw=(8.0, 8.0),
        pv_generation_kw=(0.0, 0.0),
        prices_per_kwh=(1.0, 1.0),
        slot_hours=1.0,
        battery=BatterySpec(
            capacity_kwh=10.0, max_charge_kw=4.0, max_discharge_kw=3.0,
            initial_soc_kwh=5.0,
        ),
        max_grid_import_kw=6.0,
    )
    result = simulate_asset_dispatch(request)
    assert [row.grid_import_kw for row in result.slots] == pytest.approx([6.0, 6.0])
    assert result.cap_violation_slots == ()


def test_grid_charging_is_explicit_and_respects_import_cap() -> None:
    request = AssetDispatchRequest(
        base_load_kw=(2.0,),
        pv_generation_kw=(0.0,),
        prices_per_kwh=(0.1,),
        slot_hours=1.0,
        battery=BatterySpec(
            capacity_kwh=5.0, max_charge_kw=4.0, max_discharge_kw=2.0,
            initial_soc_kwh=0.0,
        ),
        max_grid_import_kw=4.0,
        grid_charge_price_cap=0.2,
    )
    row = simulate_asset_dispatch(request).slots[0]
    assert row.battery_charge_kw == pytest.approx(2.0)
    assert row.grid_import_kw == pytest.approx(4.0)


def test_reports_unavoidable_grid_cap_violation() -> None:
    request = AssetDispatchRequest(
        base_load_kw=(10.0,),
        pv_generation_kw=(0.0,),
        prices_per_kwh=(1.0,),
        slot_hours=1.0,
        battery=BatterySpec(
            capacity_kwh=1.0, max_charge_kw=1.0, max_discharge_kw=1.0,
            initial_soc_kwh=0.0,
        ),
        max_grid_import_kw=5.0,
    )
    result = simulate_asset_dispatch(request)
    assert result.cap_violation_slots == (0,)
    assert result.slots[0].grid_cap_exceeded_kw == pytest.approx(5.0)


def test_emissions_are_reported_only_when_factors_are_supplied() -> None:
    base = {
        "base_load_kw": (3.0,),
        "pv_generation_kw": (1.0,),
        "prices_per_kwh": (2.0,),
        "slot_hours": 1.0,
        "battery": BatterySpec(
            capacity_kwh=2.0, max_charge_kw=1.0, max_discharge_kw=1.0
        ),
    }
    without_factor = simulate_asset_dispatch(AssetDispatchRequest(**base))
    with_factor = simulate_asset_dispatch(AssetDispatchRequest(
        **base, carbon_intensity_kg_per_kwh=(0.4,)
    ))
    assert without_factor.total_emissions_kg is None
    assert with_factor.total_emissions_kg == pytest.approx(0.8)


def test_rejects_mismatched_series_and_invalid_battery() -> None:
    with pytest.raises(ValueError):
        AssetDispatchRequest(
            base_load_kw=(1.0,), pv_generation_kw=(1.0, 2.0),
            prices_per_kwh=(1.0,), slot_hours=1.0,
            battery=BatterySpec(1.0, 1.0, 1.0),
        )
    with pytest.raises(ValueError):
        BatterySpec(2.0, 1.0, 1.0, initial_soc_kwh=3.0)


def test_high_price_discharge_takes_precedence_over_grid_charge() -> None:
    request = AssetDispatchRequest(
        base_load_kw=(3.0,),
        pv_generation_kw=(0.0,),
        prices_per_kwh=(0.5,),
        slot_hours=1.0,
        battery=BatterySpec(
            capacity_kwh=5.0, max_charge_kw=2.0, max_discharge_kw=2.0,
            initial_soc_kwh=3.0,
        ),
        grid_charge_price_cap=1.0,
        discharge_price_threshold=0.4,
    )
    row = simulate_asset_dispatch(request).slots[0]
    assert row.battery_discharge_kw == pytest.approx(2.0)
    assert row.battery_charge_kw == pytest.approx(0.0)
    assert row.grid_import_kw == pytest.approx(1.0)


def test_grid_charging_does_not_create_an_import_cap_violation() -> None:
    request = AssetDispatchRequest(
        base_load_kw=(4.0,),
        pv_generation_kw=(0.0,),
        prices_per_kwh=(0.1,),
        slot_hours=1.0,
        battery=BatterySpec(
            capacity_kwh=5.0, max_charge_kw=3.0, max_discharge_kw=2.0,
            initial_soc_kwh=0.0,
        ),
        max_grid_import_kw=5.0,
        grid_charge_price_cap=0.2,
    )
    row = simulate_asset_dispatch(request).slots[0]
    assert row.battery_charge_kw == pytest.approx(1.0)
    assert row.grid_import_kw == pytest.approx(5.0)
    assert row.grid_cap_exceeded_kw == pytest.approx(0.0)
