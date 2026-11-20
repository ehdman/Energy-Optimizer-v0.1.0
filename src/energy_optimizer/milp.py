"""Mixed-integer linear programming scheduler powered by SciPy/HiGHS."""

from __future__ import annotations

from math import isfinite

from .models import OptimizationRequest, OptimizationResult
from .optimizer import _build_result


def optimize_milp(
    request: OptimizationRequest,
    *,
    time_limit_seconds: float = 30.0,
) -> OptimizationResult:
    """Minimize unscheduled-task count first, then energy cost."""
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

    choices: list[tuple[str, int, float]] = []
    task_choice_indices: dict[str, list[int]] = {task.task_id: [] for task in request.tasks}
    for task in request.tasks:
        for start in range(task.earliest_start, task.latest_start + 1):
            end = start + task.duration_slots
            if end > len(request.prices_per_kwh):
                continue
            cost = task.power_kw * request.slot_hours * sum(request.prices_per_kwh[start:end])
            task_choice_indices[task.task_id].append(len(choices))
            choices.append((task.task_id, start, cost))

    choice_count = len(choices)
    task_count = len(request.tasks)
    variable_count = choice_count + task_count
    penalty = 1.0 + 2.0 * sum(abs(choice[2]) for choice in choices)
    objective = np.zeros(variable_count, dtype=float)
    for index, (_, _, cost) in enumerate(choices):
        objective[index] = cost
    objective[choice_count:] = penalty

    row_count = task_count + len(request.prices_per_kwh)
    matrix = lil_matrix((row_count, variable_count), dtype=float)
    lower = np.full(row_count, -np.inf, dtype=float)
    upper = np.full(row_count, np.inf, dtype=float)
    task_indices = {task.task_id: index for index, task in enumerate(request.tasks)}
    tasks_by_id = {task.task_id: task for task in request.tasks}

    # Each task gets exactly one start choice or one unscheduled indicator.
    for task_id, indices in task_choice_indices.items():
        row = task_indices[task_id]
        for variable_index in indices:
            matrix[row, variable_index] = 1.0
        matrix[row, choice_count + row] = 1.0
        lower[row] = upper[row] = 1.0

    # The sum of selected task power cannot exceed remaining site capacity.
    for slot, base_load in enumerate(request.base_load_kw):
        row = task_count + slot
        for variable_index, (task_id, start, _) in enumerate(choices):
            task = tasks_by_id[task_id]
            if start <= slot < start + task.duration_slots:
                matrix[row, variable_index] = task.power_kw
        upper[row] = request.max_power_kw - base_load

    solved = milp(
        c=objective,
        integrality=np.ones(variable_count, dtype=int),
        bounds=Bounds(np.zeros(variable_count), np.ones(variable_count)),
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
