from __future__ import annotations

import pytest

from app import build_request, load_scenario


def valid_scenario() -> dict:
    return {
        "prices_per_kwh": [1.0, 2.0],
        "base_load_kw": [0.0, 0.0],
        "slot_hours": 1.0,
        "max_power_kw": 5.0,
        "tasks": [
            {
                "task_id": "pump",
                "name": "Pump",
                "power_kw": 1.5,
                "duration_slots": 1,
                "earliest_start": 0,
                "latest_start": 1,
            }
        ],
    }


def test_build_request_rejects_fractional_duration_instead_of_truncating() -> None:
    scenario = valid_scenario()
    scenario["tasks"][0]["duration_slots"] = 1.5

    with pytest.raises(TypeError, match="duration_slots must be an integer"):
        build_request(scenario)


def test_build_request_rejects_boolean_integer_fields() -> None:
    scenario = valid_scenario()
    scenario["tasks"][0]["earliest_start"] = True

    with pytest.raises(TypeError, match="earliest_start must be an integer"):
        build_request(scenario)


def test_build_request_accepts_valid_integer_fields() -> None:
    request = build_request(valid_scenario())

    assert request.tasks[0].duration_slots == 1
    assert request.tasks[0].earliest_start == 0


def test_load_scenario_limits_both_time_series() -> None:
    scenario = valid_scenario()
    scenario["base_load_kw"] = [0.0] * 10_001

    with pytest.raises(ValueError, match="intervals are supported"):
        load_scenario(__import__("json").dumps(scenario).encode("utf-8"))
