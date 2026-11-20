"""Validated domain models for energy and production-aware scheduling."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class EnergyTask:
    """A non-preemptive electrical task or production operation."""

    task_id: str
    name: str
    power_kw: float
    duration_slots: int
    earliest_start: int
    latest_start: int
    machine_id: str | None = None
    predecessors: tuple[str, ...] = ()
    due_slot: int | None = None
    priority_weight: int = 1
    delay_penalty_per_slot: float = 0.0

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id cannot be empty")
        if not self.name.strip():
            raise ValueError("name cannot be empty")
        if not isfinite(self.power_kw) or self.power_kw <= 0:
            raise ValueError("power_kw must be finite and greater than zero")
        if not isinstance(self.duration_slots, int) or isinstance(self.duration_slots, bool):
            raise TypeError("duration_slots must be an integer")
        if self.duration_slots <= 0:
            raise ValueError("duration_slots must be greater than zero")
        if not isinstance(self.earliest_start, int) or isinstance(self.earliest_start, bool):
            raise TypeError("earliest_start must be an integer")
        if not isinstance(self.latest_start, int) or isinstance(self.latest_start, bool):
            raise TypeError("latest_start must be an integer")
        if self.earliest_start < 0:
            raise ValueError("earliest_start cannot be negative")
        if self.latest_start < self.earliest_start:
            raise ValueError("latest_start must be >= earliest_start")
        if self.machine_id is not None and not self.machine_id.strip():
            raise ValueError("machine_id cannot be empty when provided")
        if len(self.predecessors) != len(set(self.predecessors)):
            raise ValueError("predecessors must not contain duplicate task IDs")
        if any(not predecessor.strip() for predecessor in self.predecessors):
            raise ValueError("predecessor task IDs cannot be empty")
        if self.task_id in self.predecessors:
            raise ValueError("a task cannot depend on itself")
        if self.due_slot is not None:
            if not isinstance(self.due_slot, int) or isinstance(self.due_slot, bool):
                raise ValueError("due_slot must be an integer when provided")
            if self.due_slot < 0:
                raise ValueError("due_slot cannot be negative")
        if (
            not isinstance(self.priority_weight, int)
            or isinstance(self.priority_weight, bool)
            or not 1 <= self.priority_weight <= 1000
        ):
            raise ValueError("priority_weight must be an integer from 1 to 1000")
        if not isfinite(self.delay_penalty_per_slot) or self.delay_penalty_per_slot < 0:
            raise ValueError("delay_penalty_per_slot must be finite and non-negative")


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
        tasks_by_id = {task.task_id: task for task in self.tasks}
        for task in self.tasks:
            if task.latest_start + task.duration_slots > horizon:
                raise ValueError(f"task {task.task_id!r} does not fit inside the horizon")
            missing = set(task.predecessors) - tasks_by_id.keys()
            if missing:
                raise ValueError(
                    f"task {task.task_id!r} references unknown predecessor(s): "
                    f"{', '.join(sorted(missing))}"
                )
        _validate_dependency_graph(self.tasks)


def _validate_dependency_graph(tasks: tuple[EnergyTask, ...]) -> None:
    """Reject cyclic operation graphs before solving."""
    successors: dict[str, list[str]] = {task.task_id: [] for task in tasks}
    indegree = {task.task_id: len(task.predecessors) for task in tasks}
    for task in tasks:
        for predecessor in task.predecessors:
            successors[predecessor].append(task.task_id)
    ready = [task_id for task_id, degree in indegree.items() if degree == 0]
    visited = 0
    while ready:
        current = ready.pop()
        visited += 1
        for successor in successors[current]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
    if visited != len(tasks):
        raise ValueError("task predecessor relationships must be acyclic")


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    task_id: str
    name: str
    start_slot: int
    end_slot_exclusive: int
    energy_kwh: float
    cost: float
    machine_id: str | None = None
    priority_weight: int = 1
    late_slots: int = 0
    delay_penalty: float = 0.0


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
    total_delay_penalty: float = 0.0
    scheduled_priority_weight: int = 0
    late_task_count: int = 0
