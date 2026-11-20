"""A transparent greedy heuristic for flexible-load scheduling."""

from __future__ import annotations

from .models import OptimizationRequest, OptimizationResult, ScheduledTask


def optimize_schedule(request: OptimizationRequest) -> OptimizationResult:
    """Schedule flexible tasks in low-cost slots without exceeding the power cap.

    Tasks with fewer feasible start choices are scheduled first. For each task,
    the algorithm selects the cheapest feasible consecutive window, breaking
    ties by choosing the earliest start. This is a heuristic, not a global
    optimizer; task ordering can affect the final result.
    """

    horizon = len(request.prices_per_kwh)
    added_load = [0.0] * horizon
    scheduled: list[ScheduledTask] = []
    unscheduled: list[str] = []

    ordered_tasks = sorted(
        request.tasks,
        key=lambda task: (
            task.latest_start - task.earliest_start + 1,
            -(task.power_kw * task.duration_slots),
            task.task_id,
        ),
    )

    for task in ordered_tasks:
        best_choice: tuple[float, int] | None = None

        for start in range(task.earliest_start, task.latest_start + 1):
            end = start + task.duration_slots
            if end > horizon:
                continue

            feasible = all(
                request.base_load_kw[slot] + added_load[slot] + task.power_kw
                <= request.max_power_kw + 1e-9
                for slot in range(start, end)
            )
            if not feasible:
                continue

            cost = (
                task.power_kw
                * request.slot_hours
                * sum(request.prices_per_kwh[start:end])
            )
            candidate = (cost, start)
            if best_choice is None or candidate < best_choice:
                best_choice = candidate

        if best_choice is None:
            unscheduled.append(task.task_id)
            continue

        task_cost, start = best_choice
        end = start + task.duration_slots
        for slot in range(start, end):
            added_load[slot] += task.power_kw

        energy = task.power_kw * request.slot_hours * task.duration_slots
        scheduled.append(
            ScheduledTask(
                task_id=task.task_id,
                name=task.name,
                start_slot=start,
                end_slot_exclusive=end,
                energy_kwh=energy,
                cost=task_cost,
            )
        )

    load_profile = tuple(
        base + added
        for base, added in zip(request.base_load_kw, added_load, strict=True)
    )
    base_cost = sum(
        load * request.slot_hours * price
        for load, price in zip(request.base_load_kw, request.prices_per_kwh, strict=True)
    )
    task_cost = sum(item.cost for item in scheduled)
    total_energy = sum(load_profile) * request.slot_hours

    chronological_schedule = tuple(
        sorted(scheduled, key=lambda item: (item.start_slot, item.task_id))
    )

    return OptimizationResult(
        schedule=chronological_schedule,
        unscheduled_task_ids=tuple(unscheduled),
        base_energy_cost=base_cost,
        scheduled_task_cost=task_cost,
        total_cost=base_cost + task_cost,
        total_energy_kwh=total_energy,
        peak_power_kw=max(load_profile),
        load_profile_kw=load_profile,
    )
