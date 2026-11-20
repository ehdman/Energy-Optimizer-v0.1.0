"""Local pilot dashboard for Energy Optimizer.

Run with: streamlit run app.py
This demo does not persist uploaded scenario data or control physical equipment.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from energy_optimizer import (
    EnergyTask,
    OptimizationRequest,
    build_savings_report,
    optimize_schedule,
)

ROOT = Path(__file__).resolve().parent
SAMPLE_PATH = ROOT / "examples" / "day_ahead.json"
MAX_SCENARIO_BYTES = 2 * 1024 * 1024
MAX_SLOTS = 10_000
MAX_TASKS = 5_000


def load_scenario(raw: bytes) -> dict[str, Any]:
    """Decode and apply basic size/schema guards to an uploaded JSON scenario."""
    if len(raw) > MAX_SCENARIO_BYTES:
        raise ValueError("Dosya boyutu 2 MB sınırını aşıyor.")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Dosya geçerli UTF-8 JSON değil.") from exc
    if not isinstance(data, dict):
        raise ValueError("Senaryo kök verisi bir JSON nesnesi olmalı.")

    required = {"prices_per_kwh", "base_load_kw", "slot_hours", "max_power_kw", "tasks"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Eksik alanlar: {', '.join(sorted(missing))}")

    if not isinstance(data["prices_per_kwh"], list) or not isinstance(data["base_load_kw"], list):
        raise ValueError("prices_per_kwh ve base_load_kw listeler olmalı.")
    if len(data["prices_per_kwh"]) > MAX_SLOTS:
        raise ValueError(f"En fazla {MAX_SLOTS} zaman dilimi destekleniyor.")
    if not isinstance(data["tasks"], list) or len(data["tasks"]) > MAX_TASKS:
        raise ValueError(f"tasks listesi en fazla {MAX_TASKS} görev içerebilir.")
    return data


def build_request(data: dict[str, Any]) -> OptimizationRequest:
    tasks = tuple(
        EnergyTask(
            task_id=str(item["task_id"]),
            name=str(item["name"]),
            power_kw=float(item["power_kw"]),
            duration_slots=int(item["duration_slots"]),
            earliest_start=int(item["earliest_start"]),
            latest_start=int(item["latest_start"]),
        )
        for item in data["tasks"]
    )
    return OptimizationRequest(
        prices_per_kwh=tuple(float(value) for value in data["prices_per_kwh"]),
        base_load_kw=tuple(float(value) for value in data["base_load_kw"]),
        tasks=tasks,
        slot_hours=float(data["slot_hours"]),
        max_power_kw=float(data["max_power_kw"]),
    )


def main() -> None:
    st.set_page_config(
        page_title="Energy Optimizer | Factory Pilot",
        page_icon="⚡",
        layout="wide",
    )
    st.title("⚡ Energy Optimizer")
    st.caption("Factory pilot · Esnek yük çizelgeleme ve maliyet analizi")
    st.info(
        "Bu sürüm karar destek prototipidir. Sonuçlar tahmini senaryo karşılaştırmasıdır; "
        "gerçek fatura tasarrufu garantisi değildir ve fiziksel ekipmanları kontrol etmez."
    )

    with st.sidebar:
        st.header("Senaryo")
        uploaded = st.file_uploader(
            "JSON senaryosu yükle",
            type=["json"],
            max_upload_size=2,
            help="Örnek şablon: examples/day_ahead.json",
        )
        st.download_button(
            "Örnek senaryoyu indir",
            data=SAMPLE_PATH.read_bytes(),
            file_name="energy-optimizer-scenario.json",
            mime="application/json",
            use_container_width=True,
        )

    raw = uploaded.getvalue() if uploaded is not None else SAMPLE_PATH.read_bytes()
    try:
        scenario = load_scenario(raw)
        request = build_request(scenario)
        result = optimize_schedule(request)
        report = build_savings_report(request, result)
    except (ValueError, KeyError, TypeError, OverflowError) as exc:
        st.error(f"Senaryo işlenemedi: {exc}")
        st.stop()

    currency = str(scenario.get("currency", "para birimi"))
    slot_hours = request.slot_hours
    st.subheader(str(scenario.get("site_name", "Örnek tesis")))
    st.caption(
        f"{len(request.prices_per_kwh)} zaman dilimi · {slot_hours:g} saat/dilim · "
        f"Azami güç {request.max_power_kw:g} kW · {len(request.tasks)} esnek yük"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Referans maliyet",
        f"{report.reference_cost:,.2f} {currency}",
        help="Optimizasyon tarafından yerleştirilen aynı görevlerin en erken başlangıç saatinde çalıştığı karşılaştırma senaryosu.",
    )
    col2.metric(
        "Optimize maliyet",
        f"{report.optimized_cost:,.2f} {currency}",
    )
    col3.metric(
        "Tahmini maliyet farkı",
        f"{report.estimated_savings:,.2f} {currency}",
        f"%{report.estimated_savings_percent:.1f}",
        delta_color="normal",
        help="Aynı miktarda çizelgelenmiş iş için referans senaryo ile optimizasyon arasındaki model farkı. Gerçekleşmiş fatura tasarrufu değildir.",
    )
    col4.metric(
        "Optimize tepe güç",
        f"{report.optimized_peak_power_kw:,.2f} kW",
        f"Limit {request.max_power_kw:g} kW",
    )

    st.subheader("Yük profili")
    chart_data = {
        "Referans (kW)": list(report.reference_load_profile_kw),
        "Optimize (kW)": list(result.load_profile_kw),
        "Güç sınırı (kW)": [request.max_power_kw] * len(result.load_profile_kw),
    }
    st.line_chart(chart_data, y_label="Güç (kW)", x_label="Zaman dilimi")

    st.subheader("Önerilen çalışma planı")
    if result.schedule:
        st.dataframe(
            [
                {
                    "Görev": item.name,
                    "Başlangıç dilimi": item.start_slot,
                    "Bitiş dilimi (hariç)": item.end_slot_exclusive,
                    "Enerji (kWh)": round(item.energy_kwh, 3),
                    f"Maliyet ({currency})": round(item.cost, 2),
                }
                for item in result.schedule
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.warning("Bu senaryoda hiçbir esnek yük çizelgelenemedi.")

    if result.unscheduled_task_ids:
        st.warning(
            "Güç sınırı veya zaman penceresi nedeniyle çizelgelenemeyen görevler: "
            + ", ".join(result.unscheduled_task_ids)
        )

    st.subheader("Enerji özeti")
    left, right = st.columns(2)
    left.metric("Toplam enerji", f"{result.total_energy_kwh:,.2f} kWh")
    right.metric("Referans tepe güç", f"{report.reference_peak_power_kw:,.2f} kW")

    report_payload = {
        "report_type": "modelled_scenario_comparison",
        "currency": currency,
        "reference_cost": report.reference_cost,
        "optimized_cost": report.optimized_cost,
        "estimated_savings": report.estimated_savings,
        "estimated_savings_percent": report.estimated_savings_percent,
        "reference_peak_power_kw": report.reference_peak_power_kw,
        "optimized_peak_power_kw": report.optimized_peak_power_kw,
        "total_energy_kwh": result.total_energy_kwh,
        "schedule": [
            {
                "task_id": item.task_id,
                "name": item.name,
                "start_slot": item.start_slot,
                "end_slot_exclusive": item.end_slot_exclusive,
                "energy_kwh": item.energy_kwh,
                "cost": item.cost,
            }
            for item in result.schedule
        ],
        "unscheduled_task_ids": list(result.unscheduled_task_ids),
        "notes": [
            "This is an estimated scenario comparison, not an audited bill saving.",
            "The reference scenario uses earliest allowed start times for scheduled tasks only.",
            "Validate tariffs, taxes, demand charges, production constraints, and meter data before commercial use.",
        ],
    }
    st.download_button(
        "Optimizasyon raporunu JSON indir",
        data=json.dumps(report_payload, ensure_ascii=False, indent=2),
        file_name="energy-optimizer-report.json",
        mime="application/json",
    )

    with st.expander("Hesaplama ve güven sınırları"):
        st.write(
            "Karşılaştırma, optimizasyon motorunun çizelgeleyebildiği görevleri referans "
            "senaryoda en erken izin verilen başlangıçlarında çalıştırır. Referans güç profili "
            "tesis limitini aşabilir. Çizelgelenemeyen görevler tasarruf hesabına dahil edilmez."
        )
        st.write(
            "Bu prototip; reaktif enerji, dağıtım bedelleri, vergi, sözleşme gücü, talep "
            "aşım bedeli, üretim miktarı, hava koşulları ve gerçek zaman damgalarını henüz "
            "modellemez. Sonuçlar işletme kararı öncesinde uzman tarafından doğrulanmalıdır."
        )


if __name__ == "__main__":
    main()
