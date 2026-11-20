from __future__ import annotations

import pytest

from energy_optimizer import (
    analyze_consumption,
    compare_measured_periods,
    read_meter_data,
)


def meter_csv(rows: str) -> bytes:
    return (
        "timestamp,price_per_kwh,base_load_kw,production_units\n" + rows
    ).encode("utf-8")


def test_csv_import_infers_interval_and_production():
    data = read_meter_data(
        "baseline.csv",
        meter_csv(
            "2026-01-01T00:00:00+03:00,2.0,10.0,5\n"
            "2026-01-01T01:00:00+03:00,1.0,12.0,6\n"
            "2026-01-01T02:00:00+03:00,3.0,8.0,4\n"
        ),
    )
    assert data.slot_hours == pytest.approx(1.0)
    summary = analyze_consumption(data)
    assert summary.total_energy_kwh == pytest.approx(30.0)
    assert summary.total_cost == pytest.approx(56.0)
    assert summary.peak_power_kw == pytest.approx(12.0)
    assert summary.energy_per_production_unit == pytest.approx(2.0)


def test_accepts_total_import_power_column():
    data = read_meter_data(
        "import.csv",
        (
            "timestamp,price_per_kwh,import_power_kw\n"
            "2026-01-01T00:00:00+03:00,2.0,15.0\n"
            "2026-01-01T01:00:00+03:00,2.0,16.0\n"
        ).encode("utf-8"),
    )
    assert data.power_column == "import_power_kw"
    assert data.base_load_kw == (15.0, 16.0)


def test_rejects_both_power_columns():
    raw = (
        "timestamp,price_per_kwh,base_load_kw,import_power_kw\n"
        "2026-01-01T00:00:00+03:00,2.0,10.0,15.0\n"
        "2026-01-01T01:00:00+03:00,2.0,10.0,16.0\n"
    ).encode("utf-8")
    with pytest.raises(ValueError, match="exactly one power column"):
        read_meter_data("meter.csv", raw)


def test_rejects_naive_timestamps():
    with pytest.raises(ValueError, match="explicit UTC offset"):
        read_meter_data(
            "meter.csv",
            meter_csv(
                "2026-01-01T00:00:00,2.0,10.0,5\n"
                "2026-01-01T01:00:00,2.0,10.0,5\n"
            ),
        )


def test_rejects_irregular_intervals():
    with pytest.raises(ValueError, match="evenly spaced"):
        read_meter_data(
            "meter.csv",
            meter_csv(
                "2026-01-01T00:00:00+03:00,2.0,10.0,5\n"
                "2026-01-01T01:00:00+03:00,2.0,10.0,5\n"
                "2026-01-01T03:00:00+03:00,2.0,10.0,5\n"
            ),
        )


def test_rejects_partial_production_series():
    with pytest.raises(ValueError, match="production_units"):
        read_meter_data(
            "meter.csv",
            meter_csv(
                "2026-01-01T00:00:00+03:00,2.0,10.0,5\n"
                "2026-01-01T01:00:00+03:00,2.0,10.0,\n"
            ),
        )


def test_production_normalized_period_comparison():
    baseline = read_meter_data(
        "baseline.csv",
        meter_csv(
            "2026-01-01T00:00:00+03:00,2.0,10.0,5\n"
            "2026-01-01T01:00:00+03:00,2.0,10.0,5\n"
        ),
    )
    reporting = read_meter_data(
        "reporting.csv",
        meter_csv(
            "2026-02-01T00:00:00+03:00,3.0,8.0,5\n"
            "2026-02-01T01:00:00+03:00,3.0,8.0,5\n"
        ),
    )
    comparison = compare_measured_periods(baseline, reporting)
    assert comparison.baseline_energy_per_unit == pytest.approx(2.0)
    assert comparison.reporting_energy_per_unit == pytest.approx(1.6)
    assert comparison.normalized_energy_savings_kwh == pytest.approx(4.0)
    assert comparison.normalized_energy_savings_percent == pytest.approx(20.0)
    assert comparison.normalized_cost_savings_estimate == pytest.approx(12.0)
