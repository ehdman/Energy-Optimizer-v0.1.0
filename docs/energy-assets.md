# Energy asset dispatch (non-forecasting)

The `energy_optimizer.assets` module provides a deterministic, transparent simulation of PV self-consumption and battery dispatch. It is a planning/reporting component only: it does not connect to an inverter, BMS, PLC, SCADA, or any physical actuator.

## Inputs

- Site base load and PV generation in kW for each interval.
- Energy price in a consistent currency per kWh.
- Interval duration in hours.
- Battery capacity, charge/discharge power limits, efficiencies, minimum/maximum state of charge, and initial state of charge.
- Optional grid import cap, carbon-intensity series, export credit, grid-charge price ceiling, and discharge price threshold.

All time series must have the same non-zero length. Battery state of charge is validated against its physical capacity.

## Dispatch policy

1. PV serves site load first.
2. Remaining PV surplus charges the battery within its power and state-of-charge limits.
3. Remaining PV surplus is exported.
4. The battery discharges to reduce import above a configured grid cap, or when an explicit price threshold is reached.
5. Grid charging is disabled by default. When enabled, it is limited by the configured price ceiling, battery limits, and remaining grid-cap headroom.

The policy is deterministic and uses only the interval's supplied values. It does not forecast future load, prices, solar generation, or carbon intensity, and it does not claim global optimality.

## Outputs and safeguards

The result includes interval-by-interval PV use/export, battery charge/discharge, state of charge, grid import, energy cost, optional emissions, and any grid-cap exceedance. A cap exceedance is reported rather than hidden when the battery lacks sufficient energy or power.

Carbon emissions are calculated only when the caller supplies a time-aligned carbon-intensity series. Export credit defaults to zero. No carbon factor, tariff, or export compensation is inferred.

## Example

```python
from energy_optimizer import (
    AssetDispatchRequest,
    BatterySpec,
    simulate_asset_dispatch,
)

request = AssetDispatchRequest(
    base_load_kw=(12.0, 14.0, 10.0),
    pv_generation_kw=(8.0, 4.0, 0.0),
    prices_per_kwh=(2.0, 3.0, 1.5),
    slot_hours=0.25,
    battery=BatterySpec(
        capacity_kwh=20.0,
        max_charge_kw=5.0,
        max_discharge_kw=5.0,
        initial_soc_kwh=8.0,
    ),
    max_grid_import_kw=12.0,
)
result = simulate_asset_dispatch(request)
print(result.peak_grid_import_kw, result.total_energy_cost)
```

This simulator is not a substitute for inverter limits, battery warranty constraints, electrical protection, site commissioning, or an operator-approved safety case.
