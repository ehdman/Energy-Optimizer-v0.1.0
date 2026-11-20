from __future__ import annotations

import pytest

from energy_optimizer import EnergyTask, OptimizationRequest, optimize_schedule


def request(tasks):
    return OptimizationRequest(
        prices_per_kwh=(5.0, 1.0, 2.0, 4.0),
        base_load_kw=(1.0, 1.0, 1.0, 1.0),
        tasks=tuple(tasks),
        slot_hours=1.0,
        max_power_kw=8.0,
    )


def test_milp_finds_lowest_cost_feasible_schedule():
    tasks = [
        EnergyTask("long", "Long task", 4.0, 2, 0, 2),
        EnergyTask("short", "Short task", 3.0, 1, 0, 3),
    ]
    milp = optimize_schedule(request(tasks), solver="milp")
    greedy = optimize_schedule(request(tasks), solver="greedy")

    assert milp.solver_name == "scipy.milp"
    assert milp.is_optimal
    assert not milp.unscheduled_task_ids
    assert milp.total_cost <= greedy.total_cost + 1e-8
    assert max(milp.load_profile_kw) <= 8.0


def test_milp_maximizes_scheduled_task_count_before_cost():
    tasks = [
        EnergyTask("a", "A", 7.0, 2, 0, 0),
        EnergyTask("b", "B", 2.0, 2, 0, 2),
    ]
    result = optimize_schedule(request(tasks), solver="milp")
    assert len(result.schedule) == 2
    assert result.unscheduled_task_ids == ()


def test_milp_handles_no_tasks():
    empty = OptimizationRequest(
        prices_per_kwh=(1.0, 2.0),
        base_load_kw=(2.0, 3.0),
        tasks=(),
        slot_hours=1.0,
        max_power_kw=10.0,
    )
    result = optimize_schedule(empty, solver="milp")
    assert result.is_optimal
    assert result.schedule == ()
    assert result.total_energy_kwh == pytest.approx(5.0)


def test_milp_rejects_invalid_time_limit():
    with pytest.raises(ValueError, match="time_limit_seconds"):
        from energy_optimizer.milp import optimize_milp
        optimize_milp(request([]), time_limit_seconds=0)
