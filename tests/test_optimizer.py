from __future__ import annotations

import pytest

from energy_optimizer import EnergyTask, OptimizationRequest, optimize_schedule


def make_request(*, prices, base, tasks, cap=10.0, slot_hours=1.0):
    return OptimizationRequest(
        prices_per_kwh=tuple(prices),
        base_load_kw=tuple(base),
        tasks=tuple(tasks),
        slot_hours=slot_hours,
        max_power_kw=cap,
    )


def test_task_is_placed_in_cheapest_feasible_window():
    task = EnergyTask("pump", "Pump", 2.0, 1, 0, 2)
    result = optimize_schedule(
        make_request(prices=[3.0, 1.0, 2.0], base=[1.0, 1.0, 1.0], tasks=[task])
    )
    assert result.schedule[0].start_slot == 1
    assert result.schedule[0].cost == pytest.approx(2.0)


def test_power_cap_is_never_exceeded():
    tasks = [
        EnergyTask("a", "A", 6.0, 2, 0, 1),
        EnergyTask("b", "B", 3.0, 2, 0, 1),
    ]
    result = optimize_schedule(
        make_request(prices=[1.0, 1.0, 1.0], base=[2.0, 2.0, 2.0], tasks=tasks, cap=10.0)
    )
    assert max(result.load_profile_kw) <= 10.0
    assert result.peak_power_kw <= 10.0


def test_task_is_reported_when_no_slot_is_feasible():
    task = EnergyTask("large", "Large load", 5.0, 1, 0, 1)
    result = optimize_schedule(
        make_request(prices=[1.0, 1.0], base=[8.0, 8.0], tasks=[task], cap=10.0)
    )
    assert result.schedule == ()
    assert result.unscheduled_task_ids == ("large",)


def test_cost_includes_base_load_and_scheduled_tasks():
    task = EnergyTask("small", "Small load", 2.0, 1, 0, 1)
    result = optimize_schedule(
        make_request(prices=[2.0, 1.0], base=[1.0, 1.0], tasks=[task])
    )
    assert result.base_energy_cost == pytest.approx(3.0)
    assert result.scheduled_task_cost == pytest.approx(2.0)
    assert result.total_cost == pytest.approx(5.0)


def test_invalid_task_window_is_rejected():
    with pytest.raises(ValueError, match="does not fit"):
        OptimizationRequest(
            prices_per_kwh=(1.0, 2.0),
            base_load_kw=(0.0, 0.0),
            tasks=(EnergyTask("x", "X", 1.0, 2, 1, 1),),
            slot_hours=1.0,
            max_power_kw=5.0,
        )
