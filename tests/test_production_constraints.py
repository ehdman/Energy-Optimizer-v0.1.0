from __future__ import annotations

import pytest

from energy_optimizer import EnergyTask, OptimizationRequest, optimize_schedule


def request(tasks, *, prices=(2.0, 1.0, 3.0, 2.0), base=(1.0, 1.0, 1.0, 1.0), cap=10.0):
    return OptimizationRequest(
        prices_per_kwh=tuple(prices),
        base_load_kw=tuple(base),
        tasks=tuple(tasks),
        slot_hours=1.0,
        max_power_kw=cap,
    )


def assert_precedence(result, predecessor_id, successor_id):
    scheduled = {item.task_id: item for item in result.schedule}
    if successor_id in scheduled:
        assert predecessor_id in scheduled
        assert scheduled[predecessor_id].end_slot_exclusive <= scheduled[successor_id].start_slot


@pytest.mark.parametrize("solver", ["milp", "greedy"])
def test_predecessor_must_finish_before_successor(solver):
    tasks = [
        EnergyTask("cut", "Cut material", 2.0, 2, 0, 2, machine_id="CUTTER"),
        EnergyTask(
            "drill", "Drill part", 2.0, 1, 0, 3,
            machine_id="DRILL", predecessors=("cut",),
        ),
    ]
    result = optimize_schedule(request(tasks), solver=solver)
    assert not result.unscheduled_task_ids
    assert_precedence(result, "cut", "drill")


@pytest.mark.parametrize("solver", ["milp", "greedy"])
def test_operations_on_same_machine_never_overlap(solver):
    tasks = [
        EnergyTask("a", "Operation A", 2.0, 2, 0, 2, machine_id="M1"),
        EnergyTask("b", "Operation B", 2.0, 2, 0, 2, machine_id="M1"),
    ]
    result = optimize_schedule(request(tasks), solver=solver)
    scheduled = {item.task_id: item for item in result.schedule}
    assert set(scheduled) == {"a", "b"}
    assert (
        scheduled["a"].end_slot_exclusive <= scheduled["b"].start_slot
        or scheduled["b"].end_slot_exclusive <= scheduled["a"].start_slot
    )


@pytest.mark.parametrize("solver", ["milp", "greedy"])
def test_successor_is_not_scheduled_when_predecessor_is_infeasible(solver):
    tasks = [
        EnergyTask("prepare", "Prepare", 20.0, 1, 0, 0, machine_id="M1"),
        EnergyTask(
            "finish", "Finish", 1.0, 1, 0, 3,
            machine_id="M2", predecessors=("prepare",),
        ),
    ]
    result = optimize_schedule(request(tasks, cap=10.0), solver=solver)
    assert set(result.unscheduled_task_ids) == {"prepare", "finish"}
    assert result.schedule == ()


def test_priority_weight_decides_which_operation_is_preserved():
    tasks = [
        EnergyTask("low", "Low priority", 6.0, 2, 0, 0, priority_weight=1),
        EnergyTask("high", "High priority", 6.0, 2, 0, 0, priority_weight=10),
    ]
    result = optimize_schedule(request(tasks, cap=7.0), solver="milp")
    assert [item.task_id for item in result.schedule] == ["high"]


def test_soft_due_slot_is_visible_without_changing_bill_cost():
    task = EnergyTask(
        "pack", "Pack order", 2.0, 2, 1, 2,
        due_slot=2, delay_penalty_per_slot=3.0,
    )
    result = optimize_schedule(request([task]), solver="milp")
    assert result.schedule[0].late_slots == 1
    assert result.total_delay_penalty == pytest.approx(3.0)
    assert result.scheduled_task_cost == pytest.approx(result.schedule[0].cost)


def test_dependency_cycles_are_rejected():
    tasks = (
        EnergyTask("a", "A", 1.0, 1, 0, 2, predecessors=("b",)),
        EnergyTask("b", "B", 1.0, 1, 0, 2, predecessors=("a",)),
    )
    with pytest.raises(ValueError, match="acyclic"):
        request(tasks)


def test_unknown_predecessor_is_rejected():
    with pytest.raises(ValueError, match="unknown predecessor"):
        request([EnergyTask("b", "B", 1.0, 1, 0, 2, predecessors=("missing",))])


def test_legacy_tasks_without_production_fields_remain_valid():
    task = EnergyTask("pump", "Pump", 2.0, 1, 0, 2)
    result = optimize_schedule(request([task]), solver="milp")
    assert result.schedule[0].task_id == "pump"
    assert result.schedule[0].machine_id is None


def test_invalid_priority_and_penalty_are_rejected():
    with pytest.raises(ValueError, match="priority_weight"):
        EnergyTask("a", "A", 1.0, 1, 0, 1, priority_weight=0)
    with pytest.raises(ValueError, match="delay_penalty"):
        EnergyTask("b", "B", 1.0, 1, 0, 1, delay_penalty_per_slot=-1.0)
