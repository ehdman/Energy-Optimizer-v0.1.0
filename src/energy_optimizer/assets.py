"""Deterministic PV and battery dispatch simulation (no forecasting or device control)."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


def _finite_non_negative(value: float, field: str) -> None:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{field} must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class BatterySpec:
    capacity_kwh: float
    max_charge_kw: float
    max_discharge_kw: float
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    min_soc_kwh: float = 0.0
    max_soc_kwh: float | None = None
    initial_soc_kwh: float = 0.0

    def __post_init__(self) -> None:
        for field in ("capacity_kwh", "max_charge_kw", "max_discharge_kw",
                      "min_soc_kwh", "initial_soc_kwh"):
            _finite_non_negative(getattr(self, field), field)
        upper = self.capacity_kwh if self.max_soc_kwh is None else self.max_soc_kwh
        _finite_non_negative(upper, "max_soc_kwh")
        if self.capacity_kwh <= 0 or self.max_charge_kw <= 0 or self.max_discharge_kw <= 0:
            raise ValueError("battery capacity and power limits must be greater than zero")
        if not 0 < self.charge_efficiency <= 1 or not 0 < self.discharge_efficiency <= 1:
            raise ValueError("battery efficiencies must be in (0, 1]")
        if not self.min_soc_kwh <= self.initial_soc_kwh <= upper <= self.capacity_kwh:
            raise ValueError("battery SOC must satisfy min <= initial <= max <= capacity")


@dataclass(frozen=True, slots=True)
class AssetDispatchRequest:
    base_load_kw: tuple[float, ...]
    pv_generation_kw: tuple[float, ...]
    prices_per_kwh: tuple[float, ...]
    slot_hours: float
    battery: BatterySpec
    max_grid_import_kw: float | None = None
    carbon_intensity_kg_per_kwh: tuple[float, ...] | None = None
    export_credit_per_kwh: float = 0.0
    grid_charge_price_cap: float | None = None
    discharge_price_threshold: float | None = None

    def __post_init__(self) -> None:
        size = len(self.base_load_kw)
        if size == 0 or len(self.pv_generation_kw) != size or len(self.prices_per_kwh) != size:
            raise ValueError("load, PV, and price series must be non-empty and equal length")
        for field, values in (("base_load_kw", self.base_load_kw),
                              ("pv_generation_kw", self.pv_generation_kw),
                              ("prices_per_kwh", self.prices_per_kwh)):
            for value in values:
                if not isfinite(value) or (field != "prices_per_kwh" and value < 0):
                    raise ValueError(f"{field} values must be finite; load and PV must be non-negative")
        if not isfinite(self.slot_hours) or self.slot_hours <= 0:
            raise ValueError("slot_hours must be finite and greater than zero")
        if self.max_grid_import_kw is not None:
            if not isfinite(self.max_grid_import_kw) or self.max_grid_import_kw <= 0:
                raise ValueError("max_grid_import_kw must be finite and greater than zero")
        if self.carbon_intensity_kg_per_kwh is not None:
            if len(self.carbon_intensity_kg_per_kwh) != size:
                raise ValueError("carbon intensity series must match the planning horizon")
            for value in self.carbon_intensity_kg_per_kwh:
                _finite_non_negative(value, "carbon intensity")
        _finite_non_negative(self.export_credit_per_kwh, "export_credit_per_kwh")
        for field in ("grid_charge_price_cap", "discharge_price_threshold"):
            value = getattr(self, field)
            if value is not None and not isfinite(value):
                raise ValueError(f"{field} must be finite")


@dataclass(frozen=True, slots=True)
class AssetDispatchSlot:
    slot: int
    pv_used_kw: float
    pv_export_kw: float
    battery_charge_kw: float
    battery_discharge_kw: float
    grid_import_kw: float
    state_of_charge_kwh: float
    energy_cost: float
    emissions_kg: float | None
    grid_cap_exceeded_kw: float


@dataclass(frozen=True, slots=True)
class AssetDispatchResult:
    slots: tuple[AssetDispatchSlot, ...]
    total_grid_import_kwh: float
    total_pv_used_kwh: float
    total_pv_export_kwh: float
    total_battery_charge_kwh: float
    total_battery_discharge_kwh: float
    total_energy_cost: float
    total_emissions_kg: float | None
    peak_grid_import_kw: float
    final_state_of_charge_kwh: float
    policy: str = "pv-self-consumption + threshold dispatch"

    @property
    def cap_violation_slots(self) -> tuple[int, ...]:
        return tuple(item.slot for item in self.slots if item.grid_cap_exceeded_kw > 1e-9)


def simulate_asset_dispatch(request: AssetDispatchRequest) -> AssetDispatchResult:
    """Simulate a transparent rule-based dispatch; never sends commands to equipment.

    PV serves site load first. Surplus PV charges the battery before export.
    The battery discharges to respect the import cap, or above an explicitly
    supplied price threshold. Optional grid charging is limited to the supplied
    price ceiling and remaining import-cap headroom. No future data is inferred.
    """
    battery = request.battery
    max_soc = battery.capacity_kwh if battery.max_soc_kwh is None else battery.max_soc_kwh
    soc = battery.initial_soc_kwh
    rows: list[AssetDispatchSlot] = []

    for slot, (load, pv, price) in enumerate(zip(
        request.base_load_kw, request.pv_generation_kw, request.prices_per_kwh, strict=True
    )):
        pv_used = min(load, pv)
        surplus = max(0.0, pv - pv_used)
        net_load = load - pv_used
        charge_kw = 0.0
        discharge_kw = 0.0

        # Charge from otherwise-exported PV first.
        charge_headroom_kw = max(0.0, (max_soc - soc) / (request.slot_hours * battery.charge_efficiency))
        charge_kw = min(surplus, battery.max_charge_kw, charge_headroom_kw)
        soc += charge_kw * request.slot_hours * battery.charge_efficiency
        surplus -= charge_kw

        cap = request.max_grid_import_kw
        must_discharge = cap is not None and net_load > cap
        price_discharge = (
            request.discharge_price_threshold is not None
            and price >= request.discharge_price_threshold
        )
        if must_discharge or price_discharge:
            target = max(0.0, net_load - cap) if must_discharge and cap is not None else net_load
            available_kw = max(
                0.0, (soc - battery.min_soc_kwh) * battery.discharge_efficiency / request.slot_hours
            )
            discharge_kw = min(target, battery.max_discharge_kw, available_kw)
            soc -= discharge_kw * request.slot_hours / battery.discharge_efficiency
            net_load -= discharge_kw

        # Grid charging is opt-in and only occurs below a customer-set price cap.
        if (
            request.grid_charge_price_cap is not None
            and price <= request.grid_charge_price_cap
            and charge_kw < battery.max_charge_kw
        ):
            remaining_power = battery.max_charge_kw - charge_kw
            remaining_energy = max_soc - soc
            grid_charge = min(
                remaining_power,
                remaining_energy / (request.slot_hours * battery.charge_efficiency),
            )
            if cap is not None:
                grid_charge = min(grid_charge, max(0.0, cap - net_load))
            charge_kw += grid_charge
            soc += grid_charge * request.slot_hours * battery.charge_efficiency
            net_load += grid_charge

        grid_import = max(0.0, net_load)
        cost = (
            grid_import * request.slot_hours * price
            - surplus * request.slot_hours * request.export_credit_per_kwh
        )
        emissions = None
        if request.carbon_intensity_kg_per_kwh is not None:
            emissions = (
                grid_import * request.slot_hours
                * request.carbon_intensity_kg_per_kwh[slot]
            )
        violation = (
            max(0.0, grid_import - cap) if cap is not None else 0.0
        )
        rows.append(AssetDispatchSlot(
            slot=slot,
            pv_used_kw=pv_used,
            pv_export_kw=surplus,
            battery_charge_kw=charge_kw,
            battery_discharge_kw=discharge_kw,
            grid_import_kw=grid_import,
            state_of_charge_kwh=min(max_soc, max(battery.min_soc_kwh, soc)),
            energy_cost=cost,
            emissions_kg=emissions,
            grid_cap_exceeded_kw=violation,
        ))

    return AssetDispatchResult(
        slots=tuple(rows),
        total_grid_import_kwh=sum(row.grid_import_kw for row in rows) * request.slot_hours,
        total_pv_used_kwh=sum(row.pv_used_kw for row in rows) * request.slot_hours,
        total_pv_export_kwh=sum(row.pv_export_kw for row in rows) * request.slot_hours,
        total_battery_charge_kwh=sum(row.battery_charge_kw for row in rows) * request.slot_hours,
        total_battery_discharge_kwh=sum(row.battery_discharge_kw for row in rows) * request.slot_hours,
        total_energy_cost=sum(row.energy_cost for row in rows),
        total_emissions_kg=(
            sum(row.emissions_kg or 0.0 for row in rows)
            if request.carbon_intensity_kg_per_kwh is not None else None
        ),
        peak_grid_import_kw=max(row.grid_import_kw for row in rows),
        final_state_of_charge_kwh=rows[-1].state_of_charge_kwh,
    )
