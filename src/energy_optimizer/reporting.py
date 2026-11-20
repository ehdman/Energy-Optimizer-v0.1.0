"""Comparable reference-vs-optimized cost reporting.

The reference scenario places each successfully scheduled task at its earliest
allowed start. This is a transparent what-if comparison, not an audited bill
or a guarantee of realized savings.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import OptimizationRequest, OptimizationResult


@dataclass(frozen=True, slots=True)
class SavingsReport:
    """Cost and peak-power comparison for work completed in both scenarios."""

    reference_cost: float
    optimized_cost: float
    estimated_savings: float
    estimated_savings_percent: float
    reference_peak_power_kw: float
    optimized_peak_power_kw: float
    reference_load_profile_kw: tuple[float, ...]
    comparable_task_ids: tuple[str, ...]
    unscheduled_task_ids: tuple[str, ...]


def build_savings_report(
    request: OptimizationRequest,
    result: OptimizationResult,
) -> SavingsReport:
    """Compare the optimized schedule with an earliest-start reference.

    Only tasks that the optimizer successfully scheduled are included in both
    scenarios. This prevents an unscheduled task from appearing as a "saving"
    merely because its energy was omitted. The reference schedule is a price
    comparison baseline and may exceed the configured power limit.
    """

    tasks_by_id = {task.task_id: task for task in request.tasks}
    scheduled_ids = tuple(item.task_id for item in result.schedule)
    if len(scheduled_ids) != len(set(scheduled_ids)):
        raise ValueError("optimization result contains duplicate task IDs")
    if any(task_id not in tasks_by_id for task_id in scheduled_ids):
        raise ValueError("optimization result contains an unknown task ID")

    reference_load = list(request.base_load_kw)
    reference_task_cost = 0.0

    for task_id in scheduled_ids:
        task = tasks_by_id[task_id]
        start = task.earliest_start
        end = start + task.duration_slots
        for slot in range(start, end):
            reference_load[slot] += task.power_kw
        reference_task_cost += (
            task.power_kw
            * request.slot_hours
            * sum(request.prices_per_kwh[start:end])
        )

    reference_base_cost = sum(
        load * request.slot_hours * price
        for load, price in zip(
            request.base_load_kw, request.prices_per_kwh, strict=True
        )
    )
    reference_cost = reference_base_cost + reference_task_cost
    optimized_cost = result.total_cost
    savings = reference_cost - optimized_cost
    savings_percent = (savings / reference_cost * 100.0) if reference_cost > 0 else 0.0

    return SavingsReport(
        reference_cost=reference_cost,
        optimized_cost=optimized_cost,
        estimated_savings=savings,
        estimated_savings_percent=savings_percent,
        reference_peak_power_kw=max(reference_load),
        optimized_peak_power_kw=result.peak_power_kw,
        reference_load_profile_kw=tuple(reference_load),
        comparable_task_ids=scheduled_ids,
        unscheduled_task_ids=result.unscheduled_task_ids,
    )
