"""Scheduling algorithms and a common public optimizer interface."""

from __future__ import annotations

from .models import EnergyTask, OptimizationRequest, OptimizationResult, ScheduledTask


def _topological_task_order(tasks: tuple[EnergyTask, ...]) -> list[EnergyTask]:
    """Return a deterministic topological order, prioritizing important work."""
    tasks_by_id = {task.task_id: task for task in tasks}
    predecessors = {task.task_id: set(task.predecessors) for task in tasks}
    ordered: list[EnergyTask] = []
    completed: set[str] = set()
    while len(ordered) < len(tasks):
        ready = [
            tasks_by_id[task_id]
            for task_id, required in predecessors.items()
            if task_id not in completed and required <= completed
        ]
        if not ready:
            raise ValueError("task predecessor relationships must be acyclic")
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


def _build_result(
    request: OptimizationRequest,
    placements: dict[str, int],
    unscheduled: tuple[str, ...],
    *,
    solver_name: str,
    is_optimal: bool,
    mip_gap: float | None = None,
) -> OptimizationResult:
    tasks_by_id = {task.task_id: task for task in request.tasks}
    added_load = [0.0] * len(request.prices_per_kwh)
    scheduled: list[ScheduledTask] = []
    total_delay_penalty = 0.0
    for task_id, start in placements.items():
        task = tasks_by_id[task_id]
        end = start + task.duration_slots
        for slot in range(start, end):
            added_load[slot] += task.power_kw
        energy = task.power_kw * request.slot_hours * task.duration_slots
        cost = task.power_kw * request.slot_hours * sum(request.prices_per_kwh[start:end])
        late_slots = max(0, end - task.due_slot) if task.due_slot is not None else 0
        delay_penalty = late_slots * task.delay_penalty_per_slot
        total_delay_penalty += delay_penalty
        scheduled.append(
            ScheduledTask(
                task_id=task.task_id,
                name=task.name,
                start_slot=start,
                end_slot_exclusive=end,
                energy_kwh=energy,
                cost=cost,
                machine_id=task.machine_id,
                priority_weight=task.priority_weight,
                late_slots=late_slots,
                delay_penalty=delay_penalty,
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
    return OptimizationResult(
        schedule=tuple(sorted(scheduled, key=lambda item: (item.start_slot, item.task_id))),
        unscheduled_task_ids=tuple(sorted(unscheduled)),
        base_energy_cost=base_cost,
        scheduled_task_cost=task_cost,
        total_cost=base_cost + task_cost,
        total_energy_kwh=sum(load_profile) * request.slot_hours,
        peak_power_kw=max(load_profile),
        load_profile_kw=load_profile,
        solver_name=solver_name,
        is_optimal=is_optimal,
        mip_gap=mip_gap,
        total_delay_penalty=total_delay_penalty,
        scheduled_priority_weight=sum(item.priority_weight for item in scheduled),
        late_task_count=sum(item.late_slots > 0 for item in scheduled),
    )


def optimize_greedy(request: OptimizationRequest) -> OptimizationResult:
    """Fast deterministic heuristic that respects machine and precedence rules."""
    added_load = [0.0] * len(request.prices_per_kwh)
    placements: dict[str, int] = {}
    unscheduled: list[str] = []
    tasks_by_id = {task.task_id: task for task in request.tasks}

    for task in _topological_task_order(request.tasks):
        if any(predecessor not in placements for predecessor in task.predecessors):
            unscheduled.append(task.task_id)
            continue
        earliest = max(
            [task.earliest_start]
            + [
                placements[predecessor] + tasks_by_id[predecessor].duration_slots
                for predecessor in task.predecessors
            ]
        )
        best_choice: tuple[float, int] | None = None
        for start in range(earliest, task.latest_start + 1):
            end = start + task.duration_slots
            power_feasible = all(
                request.base_load_kw[slot] + added_load[slot] + task.power_kw
                <= request.max_power_kw + 1e-9
                for slot in range(start, end)
            )
            machine_feasible = True
            if task.machine_id is not None:
                for other_id, other_start in placements.items():
                    other = tasks_by_id[other_id]
                    if other.machine_id != task.machine_id:
                        continue
                    other_end = other_start + other.duration_slots
                    if start < other_end and other_start < end:
                        machine_feasible = False
                        break
            if not power_feasible or not machine_feasible:
                continue
            energy_cost = (
                task.power_kw
                * request.slot_hours
                * sum(request.prices_per_kwh[start:end])
            )
            late = max(0, end - task.due_slot) if task.due_slot is not None else 0
            candidate = (
                energy_cost + late * task.delay_penalty_per_slot,
                start,
            )
            if best_choice is None or candidate < best_choice:
                best_choice = candidate
        if best_choice is None:
            unscheduled.append(task.task_id)
            continue
        _, start = best_choice
        placements[task.task_id] = start
        for slot in range(start, start + task.duration_slots):
            added_load[slot] += task.power_kw
    return _build_result(
        request, placements, tuple(unscheduled), solver_name="greedy", is_optimal=False
    )


def optimize_schedule(
    request: OptimizationRequest,
    *,
    solver: str = "auto",
    time_limit_seconds: float = 30.0,
) -> OptimizationResult:
    """Use MILP when available, or the greedy heuristic when requested."""
    normalized = solver.strip().lower()
    if normalized == "greedy":
        return optimize_greedy(request)
    if normalized in {"milp", "auto"}:
        try:
            from .milp import optimize_milp
            return optimize_milp(request, time_limit_seconds=time_limit_seconds)
        except ImportError:
            if normalized == "milp":
                raise
            return optimize_greedy(request)
    raise ValueError("solver must be one of: auto, greedy, milp")
