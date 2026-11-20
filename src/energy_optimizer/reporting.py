"""Comparable reference-vs-optimized cost reporting."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

from .models import EnergyTask, OptimizationRequest, OptimizationResult


@dataclass(frozen=True, slots=True)
class SavingsReport:
    """Energy-cost and peak-power comparison for work completed in both scenarios."""

    reference_cost: float
    optimized_cost: float
    estimated_savings: float
    estimated_savings_percent: float
    reference_peak_power_kw: float
    optimized_peak_power_kw: float
    reference_load_profile_kw: tuple[float, ...]
    comparable_task_ids: tuple[str, ...]
    unscheduled_task_ids: tuple[str, ...]


def _ordered_scheduled_tasks(
    tasks_by_id: dict[str, EnergyTask],
    scheduled_ids: set[str],
    machine_predecessors: dict[str, set[str]],
) -> list[EnergyTask]:
    remaining = {
        task_id: set(tasks_by_id[task_id].predecessors) | machine_predecessors.get(task_id, set())
        for task_id in scheduled_ids
    }
    if any(not predecessors <= scheduled_ids for predecessors in remaining.values()):
        raise ValueError("optimization result schedules an operation without its predecessor")
    ordered: list[EnergyTask] = []
    completed: set[str] = set()
    while len(ordered) < len(scheduled_ids):
        ready = [
            tasks_by_id[task_id]
            for task_id, predecessors in remaining.items()
            if task_id not in completed and predecessors <= completed
        ]
        if not ready:
            raise ValueError("scheduled operations contain a dependency cycle")
        ready.sort(
            key=lambda task: (
                -task.priority_weight,
                task.latest_start - task.earliest_start,
                task.earliest_start,
                task.task_id,
            )
        )
        task = ready[0]
        ordered.append(task)
        completed.add(task.task_id)
    return ordered


def build_savings_report(
    request: OptimizationRequest,
    result: OptimizationResult,
) -> SavingsReport:
    """Compare completed work with an earliest feasible reference schedule.

    The reference respects declared predecessor and machine constraints but,
    like the previous reference, does not enforce the site power cap. Only
    operations successfully scheduled by the optimizer are included.
    """
    tasks_by_id = {task.task_id: task for task in request.tasks}
    scheduled_ids = {item.task_id for item in result.schedule}
    if len(scheduled_ids) != len(result.schedule):
        raise ValueError("optimization result contains duplicate task IDs")
    if not scheduled_ids <= tasks_by_id.keys():
        raise ValueError("optimization result contains an unknown task ID")

    # Preserve the machine order selected by the optimizer. This guarantees a
    # feasible reference sequence while allowing each operation to move earlier.
    machine_sequences: dict[str, list[tuple[int, str]]] = {}
    for item in result.schedule:
        if item.machine_id is not None:
            machine_sequences.setdefault(item.machine_id, []).append((item.start_slot, item.task_id))
    machine_predecessors: dict[str, set[str]] = {}
    for sequence in machine_sequences.values():
        sequence.sort()
        for previous, current in pairwise(sequence):
            machine_predecessors.setdefault(current[1], set()).add(previous[1])

    reference_load = list(request.base_load_kw)
    reference_task_cost = 0.0
    reference_placements: dict[str, int] = {}

    for task in _ordered_scheduled_tasks(tasks_by_id, scheduled_ids, machine_predecessors):
        all_predecessors = set(task.predecessors) | machine_predecessors.get(task.task_id, set())
        predecessor_finish = [
            reference_placements[pred] + tasks_by_id[pred].duration_slots
            for pred in all_predecessors
        ]
        earliest = max([task.earliest_start] + predecessor_finish)
        reference_start: int | None = None
        for start in range(earliest, task.latest_start + 1):
            end = start + task.duration_slots
            machine_available = True
            if task.machine_id is not None:
                for other_id, other_start in reference_placements.items():
                    other = tasks_by_id[other_id]
                    if other.machine_id != task.machine_id:
                        continue
                    other_end = other_start + other.duration_slots
                    if start < other_end and other_start < end:
                        machine_available = False
                        break
            if machine_available:
                reference_start = start
                break
        if reference_start is None:
            raise ValueError("could not construct a feasible machine-aware reference schedule")

        reference_placements[task.task_id] = reference_start
        end = reference_start + task.duration_slots
        for slot in range(reference_start, end):
            reference_load[slot] += task.power_kw
        reference_task_cost += (
            task.power_kw
            * request.slot_hours
            * sum(request.prices_per_kwh[reference_start:end])
        )

    reference_base_cost = sum(
        load * request.slot_hours * price
        for load, price in zip(request.base_load_kw, request.prices_per_kwh, strict=True)
    )
    reference_cost = reference_base_cost + reference_task_cost
    optimized_cost = result.total_cost
    savings = reference_cost - optimized_cost
    savings_percent = savings / reference_cost * 100.0 if reference_cost > 0 else 0.0

    return SavingsReport(
        reference_cost=reference_cost,
        optimized_cost=optimized_cost,
        estimated_savings=savings,
        estimated_savings_percent=savings_percent,
        reference_peak_power_kw=max(reference_load),
        optimized_peak_power_kw=result.peak_power_kw,
        reference_load_profile_kw=tuple(reference_load),
        comparable_task_ids=tuple(
            item.task_id for item in result.schedule
        ),
        unscheduled_task_ids=result.unscheduled_task_ids,
    )
