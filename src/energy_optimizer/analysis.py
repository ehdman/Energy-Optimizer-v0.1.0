"""Consumption analytics and measured-period comparison."""

from __future__ import annotations

from dataclasses import dataclass

from .ingestion import MeterData


@dataclass(frozen=True, slots=True)
class ConsumptionSummary:
    interval_count: int
    duration_hours: float
    total_energy_kwh: float
    total_cost: float
    average_power_kw: float
    peak_power_kw: float
    minimum_power_kw: float
    load_factor: float
    average_price_per_kwh: float
    production_units: float | None
    energy_per_production_unit: float | None
    peak_timestamps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MeasuredSavingsComparison:
    baseline: ConsumptionSummary
    reporting: ConsumptionSummary
    raw_energy_change_kwh: float
    raw_energy_change_percent: float
    raw_cost_change: float
    raw_cost_change_percent: float
    baseline_energy_per_unit: float | None
    reporting_energy_per_unit: float | None
    normalized_energy_savings_kwh: float | None
    normalized_energy_savings_percent: float | None
    normalized_cost_savings_estimate: float | None
    interpretation: str


def analyze_consumption(data: MeterData) -> ConsumptionSummary:
    powers = [item.base_load_kw for item in data.intervals]
    total_energy = sum(power * data.slot_hours for power in powers)
    total_cost = sum(
        item.base_load_kw * data.slot_hours * item.price_per_kwh
        for item in data.intervals
    )
    peak = max(powers)
    production = data.production_units
    total_production = sum(production) if production is not None else None
    intensity = (
        total_energy / total_production
        if total_production is not None and total_production > 0
        else None
    )
    peak_times = tuple(
        item.timestamp.isoformat()
        for item in data.intervals
        if abs(item.base_load_kw - peak) <= 1e-9
    )
    return ConsumptionSummary(
        interval_count=len(data.intervals),
        duration_hours=len(data.intervals) * data.slot_hours,
        total_energy_kwh=total_energy,
        total_cost=total_cost,
        average_power_kw=sum(powers) / len(powers),
        peak_power_kw=peak,
        minimum_power_kw=min(powers),
        load_factor=(sum(powers) / len(powers) / peak) if peak > 0 else 0.0,
        average_price_per_kwh=total_cost / total_energy if total_energy > 0 else 0.0,
        production_units=total_production,
        energy_per_production_unit=intensity,
        peak_timestamps=peak_times,
    )


def compare_measured_periods(
    baseline_data: MeterData,
    reporting_data: MeterData,
) -> MeasuredSavingsComparison:
    """Compare metered periods; production-normalize when both datasets allow it."""
    if abs(baseline_data.slot_hours - reporting_data.slot_hours) > 1e-9:
        raise ValueError("Baseline and reporting files must use the same interval length")
    baseline = analyze_consumption(baseline_data)
    reporting = analyze_consumption(reporting_data)

    energy_change = baseline.total_energy_kwh - reporting.total_energy_kwh
    energy_percent = (
        energy_change / baseline.total_energy_kwh * 100.0
        if baseline.total_energy_kwh > 0 else 0.0
    )
    cost_change = baseline.total_cost - reporting.total_cost
    cost_percent = (
        cost_change / baseline.total_cost * 100.0
        if baseline.total_cost > 0 else 0.0
    )

    baseline_intensity = baseline.energy_per_production_unit
    reporting_intensity = reporting.energy_per_production_unit
    normalized_energy = normalized_percent = normalized_cost = None
    if (
        baseline.production_units is not None
        and reporting.production_units is not None
        and baseline.production_units > 0
        and reporting.production_units > 0
        and baseline_intensity is not None
        and reporting_intensity is not None
    ):
        normalized_energy = (
            baseline_intensity - reporting_intensity
        ) * reporting.production_units
        normalized_percent = (
            (baseline_intensity - reporting_intensity) / baseline_intensity * 100.0
            if baseline_intensity > 0 else 0.0
        )
        normalized_cost = normalized_energy * reporting.average_price_per_kwh

    interpretation = (
        "Production-normalized energy intensity is available, but this is a measured period "
        "comparison, not proof that the software caused the difference."
        if normalized_energy is not None else
        "Production normalization is unavailable. Raw differences may reflect production "
        "volume, period length, tariffs, weather, or operating conditions; do not label "
        "them verified savings."
    )
    return MeasuredSavingsComparison(
        baseline=baseline,
        reporting=reporting,
        raw_energy_change_kwh=energy_change,
        raw_energy_change_percent=energy_percent,
        raw_cost_change=cost_change,
        raw_cost_change_percent=cost_percent,
        baseline_energy_per_unit=baseline_intensity,
        reporting_energy_per_unit=reporting_intensity,
        normalized_energy_savings_kwh=normalized_energy,
        normalized_energy_savings_percent=normalized_percent,
        normalized_cost_savings_estimate=normalized_cost,
        interpretation=interpretation,
    )
