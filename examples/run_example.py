"""Run the sample day-ahead scheduling scenario."""

from __future__ import annotations

import json
from pathlib import Path

from energy_optimizer import (
    EnergyTask,
    OptimizationRequest,
    build_savings_report,
    optimize_schedule,
)


def main() -> None:
    data_path = Path(__file__).with_name("day_ahead.json")
    data = json.loads(data_path.read_text(encoding="utf-8"))

    request = OptimizationRequest(
        prices_per_kwh=tuple(data["prices_per_kwh"]),
        base_load_kw=tuple(data["base_load_kw"]),
        slot_hours=float(data["slot_hours"]),
        max_power_kw=float(data["max_power_kw"]),
        tasks=tuple(EnergyTask(**task) for task in data["tasks"]),
    )
    result = optimize_schedule(request)
    report = build_savings_report(request, result)
    currency = data["currency"]

    print(f"Referans maliyet: {report.reference_cost:.2f} {currency}")
    print(f"Optimize maliyet: {report.optimized_cost:.2f} {currency}")
    print(
        f"Tahmini maliyet farkı: {report.estimated_savings:.2f} {currency} "
        f"(%{report.estimated_savings_percent:.1f})"
    )
    print(f"Toplam enerji: {result.total_energy_kwh:.2f} kWh")
    print(f"Optimize tepe güç: {result.peak_power_kw:.2f} kW")
    print("\nÖnerilen program:")
    for item in result.schedule:
        print(
            f"- {item.name}: slot {item.start_slot}–{item.end_slot_exclusive - 1} "
            f"| {item.energy_kwh:.2f} kWh | {item.cost:.2f} {currency}"
        )

    if result.unscheduled_task_ids:
        print("\nÇizelgelenemeyen görevler:")
        for task_id in result.unscheduled_task_ids:
            print(f"- {task_id}")

    print(
        "\nNot: Maliyet farkı, aynı çizelgelenen iş için en erken başlangıç referansına "
        "göre model tahminidir; gerçekleşmiş fatura tasarrufu değildir."
    )


if __name__ == "__main__":
    main()
