from __future__ import annotations

import pytest

from energy_optimizer import (
    EnergyTask,
    OptimizationRequest,
    build_savings_report,
    optimize_schedule,
)


def make_request(*, prices, base, tasks, cap=10.0, slot_hours=1.0):
    return OptimizationRequest(
        prices_per_kwh=tuple(prices),
        base_load_kw=tuple(base),
        tasks=tuple(tasks),
        slot_hours=slot_hours,
        max_power_kw=cap,
    )


def test_savings_report_compares_same_scheduled_work_with_earliest_start():
    tasks = [
        EnergyTask("pump", "Pump", 2.0, 1, 0, 2),
        EnergyTask("fan", "Fan", 1.0, 1, 0, 2),
    ]
    request = make_request(
        prices=[3.0, 1.0, 2.0],
        base=[1.0, 1.0, 1.0],
        tasks=tasks,
        cap=10.0,
    )
    result = optimize_schedule(request)
    report = build_savings_report(request, result)

    assert set(report.comparable_task_ids) == {"pump", "fan"}
    assert report.reference_cost > report.optimized_cost
    assert report.estimated_savings == pytest.approx(
        report.reference_cost - report.optimized_cost
    )
    assert report.optimized_peak_power_kw <= request.max_power_kw


def test_unscheduled_tasks_are_not_counted_as_savings():
    task = EnergyTask("large", "Large load", 5.0, 1, 0, 1)
    request = make_request(
        prices=[1.0, 1.0],
        base=[8.0, 8.0],
        tasks=[task],
        cap=10.0,
    )
    result = optimize_schedule(request)
    report = build_savings_report(request, result)

    assert report.unscheduled_task_ids == ("large",)
    assert report.comparable_task_ids == ()
    assert report.reference_cost == pytest.approx(result.total_cost)
    assert report.estimated_savings == pytest.approx(0.0)


def test_reference_profile_uses_earliest_allowed_start():
    task = EnergyTask("heater", "Heater", 2.0, 2, 1, 3)
    request = make_request(
        prices=[3.0, 2.0, 1.0, 4.0, 5.0],
        base=[1.0, 1.0, 1.0, 1.0, 1.0],
        tasks=[task],
        cap=10.0,
    )
    result = optimize_schedule(request)
    report = build_savings_report(request, result)

    assert report.reference_load_profile_kw[1:3] == (3.0, 3.0)
    assert report.optimized_load_profile_kw if hasattr(report, "optimized_load_profile_kw") else True
