"""Energy optimization and industrial energy analytics toolkit."""

from .analysis import (
    ConsumptionSummary,
    MeasuredSavingsComparison,
    analyze_consumption,
    compare_measured_periods,
)
from .assets import (
    AssetDispatchRequest,
    AssetDispatchResult,
    AssetDispatchSlot,
    BatterySpec,
    simulate_asset_dispatch,
)
from .ingestion import MeterData, MeterInterval, read_meter_data
from .models import EnergyTask, OptimizationRequest, OptimizationResult, ScheduledTask
from .optimizer import optimize_greedy, optimize_schedule
from .reporting import SavingsReport, build_savings_report

__all__ = [
    "AssetDispatchRequest",
    "AssetDispatchResult",
    "AssetDispatchSlot",
    "BatterySpec",
    "ConsumptionSummary",
    "EnergyTask",
    "MeasuredSavingsComparison",
    "MeterData",
    "MeterInterval",
    "OptimizationRequest",
    "OptimizationResult",
    "SavingsReport",
    "ScheduledTask",
    "analyze_consumption",
    "build_savings_report",
    "compare_measured_periods",
    "optimize_greedy",
    "optimize_schedule",
    "read_meter_data",
    "simulate_asset_dispatch",
]
