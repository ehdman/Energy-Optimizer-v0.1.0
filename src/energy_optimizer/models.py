"""Validated input and output models for the scheduling engine."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class EnergyTask:
    """A non-preemptive, flexible electrical load."""
    task_id: str
    name: str
    power_kw: float
    duration_slots: int
    earliest_start: int
    latest_start: int

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id cannot be empty")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        if not isfinite(self.power_kw) or self.power_kw <= 0:
            raise ValueError("power_kw must be finite and greater than zero")
        if self.duration_slots <= 0:
            raise ValueError("duration_slots must be greater than zero")
        if self.earliest_start < 0:
            raise ValueError("earliest_start cannot be negative")
        if self.latest_start < self.earliest_start:
            raise ValueError("latest_start must be >= earliest_start")


@dataclass(frozen=True, slots=True)
class OptimizationRequest:
    prices_per_kwh: tuple[float, ...]
    base_load_kw: tuple[float, ...]
    tasks: tuple[EnergyTask, ...]
    slot_hours: float
    max_power_kw: float

    def __post_init__(self) -> None:
        if not self.prices_per_kwh:
            raise ValueError("at least one price slot is required")
        if len(self.prices_per_kwh) != len(self.base_load_kw):
            raise ValueError("price and base-load series must have equal lengths")
        if any(not isfinite(price) for price in self.prices_per_kwh):
            raise ValueError("all prices must be finite")
        if any(not isfinite(load) or load < 0 for load in self.base_load_kw):
            raise ValueError("base loads must be finite and non-negative")
        if not isfinite(self.slot_hours) or self.slot_hours <= 0:
            raise ValueError("slot_hours must be finite and greater than zero")
        if not isfinite(self.max_power_kw) or self.max_power_kw <= 0:
            raise ValueError("max_power_kw must be finite and greater than zero")
        if any(load > self.max_power_kw for load in self.base_load_kw):
            raise ValueError("base load exceeds max_power_kw")
        horizon = len(self.prices_per_kwh)
        ids = [task.task_id for task in self.tasks]
        if len(ids) != len(set(ids)):
            raise ValueError("task_id values must be unique")
        for task in self.tasks:
            if task.latest_start + task.duration_slots > horizon:
                raise ValueError(f"task {task.task_id!r} does not fit inside the horizon")


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    task_id: str
    name: str
    start_slot: int
    end_slot_exclusive: int
    energy_kwh: float
    cost: float


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    schedule: tuple[ScheduledTask, ...]
    unscheduled_task_ids: tuple[str, ...]
    base_energy_cost: float
    scheduled_task_cost: float
    total_cost: float
    total_energy_kwh: float
    peak_power_kw: float
    load_profile_kw: tuple[float, ...]
    solver_name: str = "greedy"
    is_optimal: bool = False
    mip_gap: float | None = None
