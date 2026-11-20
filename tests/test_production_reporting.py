from __future__ import annotations

from energy_optimizer import EnergyTask, OptimizationRequest, build_savings_report, optimize_schedule


def test_reference_schedule_respects_machine_and_precedence_constraints():
    tasks = (
        EnergyTask("cut", "Cut", 2.0, 2, 0, 2, machine_id="CUTTER"),
        EnergyTask("mill", "Mill", 2.0, 1, 0, 3, machine_id="MILL", predecessors=("cut",)),
        EnergyTask("polish", "Polish", 2.0, 2, 0, 2, machine_id="CUTTER"),
    )
    request = OptimizationRequest(
        prices_per_kwh=(3.0, 2.0, 1.0, 2.0, 3.0),
        base_load_kw=(1.0,) * 5,
        tasks=tasks,
        slot_hours=1.0,
        max_power_kw=10.0,
    )
    result = optimize_schedule(request, solver="milp")
    report = build_savings_report(request, result)
    starts = {item.task_id: item.start_slot for item in result.schedule}

    assert report.comparable_task_ids
    assert starts["cut"] + 2 <= starts["mill"]
    assert (
        report.reference_load_profile_kw[0] >= 1.0
        and report.reference_peak_power_kw >= 1.0
    )
