"""Production-aware mixed-integer scheduling with SciPy/HiGHS."""

from __future__ import annotations

from math import isfinite

from .models import OptimizationRequest, OptimizationResult
from .optimizer import _build_result

# Explicit model budgets prevent oversized user scenarios from exhausting the
# dashboard process. Large planning problems should be decomposed into rolling
# horizons or sent to a dedicated solver service.
MAX_START_CHOICES = 100_000
MAX_MATRIX_NONZERO_ESTIMATE = 3_000_000


def optimize_milp(
    request: OptimizationRequest,
    *,
    time_limit_seconds: float = 30.0,
) -> OptimizationResult:
    """Maximize scheduled priority weight, then minimize energy and delay cost."""
    if not isfinite(time_limit_seconds) or time_limit_seconds <= 0:
        raise ValueError("time_limit_seconds must be finite and greater than zero")
    try:
        import numpy as np
        from scipy.optimize import Bounds, LinearConstraint, milp
        from scipy.sparse import lil_matrix
    except ImportError as exc:
        raise ImportError(
            "MILP requires SciPy. Install with: pip install -e '.[optimization]'"
        ) from exc

    if not request.tasks:
        return _build_result(
            request, {}, (), solver_name="scipy.milp", is_optimal=True, mip_gap=0.0
        )

    tasks_by_id = {task.task_id: task for task in request.tasks}
    candidate_counts = {
        task.task_id: task.latest_start - task.earliest_start + 1
        for task in request.tasks
    }
    candidate_count = sum(candidate_counts.values())
    if candidate_count > MAX_START_CHOICES:
        raise ValueError(
            f"MILP model has {candidate_count:,} possible start choices; "
            f"the configured limit is {MAX_START_CHOICES:,}. Narrow operation "
            "windows or use a shorter rolling horizon."
        )

    # The upper bound counts possible nonzero coefficients for power, machine,
    # and dependency constraints before allocating the sparse matrix.
    occupancy_estimate = sum(
        candidate_counts[task.task_id] * task.duration_slots
        for task in request.tasks
    )
    precedence_estimate = sum(
        candidate_counts[task.task_id] * candidate_counts[predecessor_id]
        for task in request.tasks
        for predecessor_id in task.predecessors
    )
    nonzero_estimate = (
        candidate_count
        + len(request.tasks)
        + 2 * occupancy_estimate
        + 2 * precedence_estimate
    )
    if nonzero_estimate > MAX_MATRIX_NONZERO_ESTIMATE:
        raise ValueError(
            f"MILP matrix estimate ({nonzero_estimate:,} nonzero entries) exceeds "
            f"the configured limit ({MAX_MATRIX_NONZERO_ESTIMATE:,}). "
            "Reduce the horizon, narrow start windows, or use a rolling horizon."
        )

    choices: list[tuple[str, int, float]] = []
    task_choice_indices: dict[str, list[int]] = {task.task_id: [] for task in request.tasks}
    for task in request.tasks:
        for start in range(task.earliest_start, task.latest_start + 1):
            end = start + task.duration_slots
            energy_cost = (
                task.power_kw
                * request.slot_hours
                * sum(request.prices_per_kwh[start:end])
            )
            late = max(0, end - task.due_slot) if task.due_slot is not None else 0
            delay_cost = late * task.delay_penalty_per_slot
            task_choice_indices[task.task_id].append(len(choices))
            choices.append((task.task_id, start, energy_cost + delay_cost))

    choice_count = len(choices)
    task_count = len(request.tasks)
    horizon = len(request.prices_per_kwh)
    penalty = 1.0 + 2.0 * sum(abs(choice[2]) for choice in choices)
    objective = np.zeros(choice_count + task_count, dtype=float)
    for index, (_, _, cost) in enumerate(choices):
        objective[index] = cost
    task_index = {task.task_id: index for index, task in enumerate(request.tasks)}
    for task in request.tasks:
        objective[choice_count + task_index[task.task_id]] = (
            penalty * task.priority_weight
        )

    machine_task_counts: dict[str, int] = {}
    for task in request.tasks:
        if task.machine_id is not None:
            machine_task_counts[task.machine_id] = (
                machine_task_counts.get(task.machine_id, 0) + 1
            )
    shared_machine_ids = {
        machine_id for machine_id, count in machine_task_counts.items() if count > 1
    }
    # Only create resource rows for machines used by multiple operations, and
    # only for slots touched by at least one candidate operation.
    machine_slots = sorted(
        {
            (task.machine_id, slot)
            for task in request.tasks
            if task.machine_id in shared_machine_ids
            for start in range(task.earliest_start, task.latest_start + 1)
            for slot in range(start, start + task.duration_slots)
        }
    )
    first_machine_row = task_count + horizon
    machine_row = {
        key: first_machine_row + index for index, key in enumerate(machine_slots)
    }

    precedence_specs: list[tuple[int, list[int]]] = []
    for task in request.tasks:
        for successor_choice in task_choice_indices[task.task_id]:
            successor_start = choices[successor_choice][1]
            for predecessor_id in task.predecessors:
                predecessor_duration = tasks_by_id[predecessor_id].duration_slots
                compatible = [
                    index
                    for index in task_choice_indices[predecessor_id]
                    if choices[index][1] + predecessor_duration <= successor_start
                ]
                precedence_specs.append((successor_choice, compatible))

    first_precedence_row = first_machine_row + len(machine_slots)
    row_count = first_precedence_row + len(precedence_specs)
    matrix = lil_matrix((row_count, choice_count + task_count), dtype=float)
    lower = np.full(row_count, -np.inf, dtype=float)
    upper = np.full(row_count, np.inf, dtype=float)

    # Each task is assigned one start choice or marked unscheduled.
    for task_id, indices in task_choice_indices.items():
        row = task_index[task_id]
        for variable_index in indices:
            matrix[row, variable_index] = 1.0
        matrix[row, choice_count + row] = 1.0
        lower[row] = upper[row] = 1.0

    # Site import-power cap and single-capacity machine resource rows.
    for variable_index, (task_id, start, _) in enumerate(choices):
        task = tasks_by_id[task_id]
        for slot in range(start, start + task.duration_slots):
            matrix[task_count + slot, variable_index] = task.power_kw
            if task.machine_id in shared_machine_ids:
                matrix[machine_row[(task.machine_id, slot)], variable_index] = 1.0
    for slot, base_load in enumerate(request.base_load_kw):
        upper[task_count + slot] = request.max_power_kw - base_load
    for row in machine_row.values():
        upper[row] = 1.0

    # Selecting an operation requires each direct predecessor to be selected
    # at a start that allows it to finish before the successor starts.
    for offset, (successor_choice, predecessor_choices) in enumerate(precedence_specs):
        row = first_precedence_row + offset
        matrix[row, successor_choice] = 1.0
        for predecessor_choice in predecessor_choices:
            matrix[row, predecessor_choice] = -1.0
        upper[row] = 0.0

    solved = milp(
        c=objective,
        integrality=np.ones(choice_count + task_count, dtype=int),
        bounds=Bounds(
            np.zeros(choice_count + task_count),
            np.ones(choice_count + task_count),
        ),
        constraints=LinearConstraint(matrix.tocsr(), lower, upper),
        options={"time_limit": float(time_limit_seconds), "mip_rel_gap": 1e-8},
    )
    if solved.x is None:
        raise RuntimeError(f"MILP solver did not produce a feasible result: {solved.message}")

    placements: dict[str, int] = {}
    unscheduled: list[str] = []
    for task in request.tasks:
        selected = [
            choices[index][1]
            for index in task_choice_indices[task.task_id]
            if solved.x[index] > 0.5
        ]
        if selected:
            placements[task.task_id] = selected[0]
        else:
            unscheduled.append(task.task_id)

    gap = getattr(solved, "mip_gap", None)
    if gap is not None and not isfinite(float(gap)):
        gap = None
    return _build_result(
        request,
        placements,
        tuple(unscheduled),
        solver_name="scipy.milp",
        is_optimal=bool(solved.success and solved.status == 0),
        mip_gap=float(gap) if gap is not None else None,
    )
