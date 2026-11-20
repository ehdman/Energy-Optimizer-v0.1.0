"""Local pilot dashboard for meter analysis and energy optimization.

Run with: streamlit run app.py
This is a local decision-support demo. It does not persist customer data or
control physical equipment and must not be exposed publicly without security work.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import streamlit as st

from energy_optimizer.ui import apply_theme

from energy_optimizer import (
    EnergyTask,
    OptimizationRequest,
    analyze_consumption,
    build_savings_report,
    compare_measured_periods,
    optimize_schedule,
    read_meter_data,
)

ROOT = Path(__file__).resolve().parent
SAMPLE_PATH = ROOT / "examples" / "production_line.json"
MAX_SCENARIO_BYTES = 2 * 1024 * 1024
MAX_SLOTS = 10_000
MAX_TASKS = 5_000


def load_scenario(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_SCENARIO_BYTES:
        raise ValueError("Scenario JSON exceeds the 2 MB size limit.")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Scenario file is not valid UTF-8 JSON.") from exc
    if not isinstance(data, dict):
        raise TypeError("Scenario root must be a JSON object.")
    required = {"prices_per_kwh", "base_load_kw", "slot_hours", "max_power_kw", "tasks"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"Missing scenario fields: {', '.join(sorted(missing))}")
    if not isinstance(data["prices_per_kwh"], list) or not isinstance(data["base_load_kw"], list):
        raise TypeError("prices_per_kwh and base_load_kw must be arrays.")
    if len(data["prices_per_kwh"]) > MAX_SLOTS:
        raise ValueError(f"At most {MAX_SLOTS} intervals are supported.")
    if not isinstance(data["tasks"], list) or len(data["tasks"]) > MAX_TASKS:
        raise ValueError(f"tasks must be an array with at most {MAX_TASKS} items.")
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
            machine_id=str(item["machine_id"]) if item.get("machine_id") is not None else None,
            predecessors=tuple(str(value) for value in item.get("predecessors", ())),
            due_slot=int(item["due_slot"]) if item.get("due_slot") is not None else None,
            priority_weight=int(item.get("priority_weight", 1)),
            delay_penalty_per_slot=float(item.get("delay_penalty_per_slot", 0.0)),
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


def run_optimizer_tab() -> None:
    st.subheader("Üretim ve enerji planlaması")
    st.caption(
        "Üretim görevlerini ve tesis güç sınırını içeren senaryoyu yükleyin. İsterseniz sayaç verisiyle gerçek tüketim profilinizi kullanın."
    )
    col_a, col_b = st.columns(2)
    with col_a:
        scenario_file = st.file_uploader(
            "Üretim senaryosu (JSON)",
            type=["json"],
            key="scenario_json",
        )
    with col_b:
        meter_file = st.file_uploader(
            "Sayaç verisi (isteğe bağlı)",
            type=["csv", "xlsx", "xlsm"],
            key="optimization_meter",
        )

    solver_label = st.selectbox(
        "Optimizasyon yöntemi",
        ["MILP (daha kapsamlı)", "Greedy (daha hızlı)"],
        help="MILP matematiksel optimizasyon kullanır. Greedy hızlı bir sezgiseldir; en iyi sonucu garanti etmez.",
    )
    solver = "milp" if solver_label.startswith("MILP") else "greedy"

    try:
        scenario_raw = (
            scenario_file.getvalue()
            if scenario_file is not None
            else SAMPLE_PATH.read_bytes()
        )
        scenario = load_scenario(scenario_raw)
        meter_data = None
        if meter_file is not None:
            meter_data = read_meter_data(meter_file.name, meter_file.getvalue())
            if meter_data.power_column != "base_load_kw":
                raise ValueError(
                    "Scheduling requires base_load_kw that excludes the flexible tasks "
                    "defined in the scenario. import_power_kw is total site import power "
                    "and belongs in the analysis/comparison tabs."
                )
            scenario = dict(scenario)
            scenario["prices_per_kwh"] = list(meter_data.prices_per_kwh)
            scenario["base_load_kw"] = list(meter_data.base_load_kw)
            scenario["slot_hours"] = meter_data.slot_hours

        request = build_request(scenario)
        result = optimize_schedule(request, solver=solver)
        report = build_savings_report(request, result)
    except ImportError as exc:
        st.error(str(exc))
        st.info('MILP için pip install -e ".[optimization]" komutunu çalıştırın.')
        return
    except (ValueError, KeyError, TypeError, OverflowError, RuntimeError) as exc:
        st.error(f"Senaryo işlenemedi: {exc}")
        return

    currency = str(scenario.get("currency", "currency units"))
    st.caption(
        f"{scenario.get('site_name', 'Sample site')} · "
        f"{len(request.prices_per_kwh)} intervals · {request.slot_hours:g} h/interval · "
        f"{len(request.tasks)} production operations"
    )
    if meter_data is not None:
        st.success(
            f"Meter data imported: {len(meter_data.intervals)} intervals, "
            f"{meter_data.slot_hours:g} h/interval."
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Referans maliyet", f"{report.reference_cost:,.2f} {currency}")
    m2.metric("Optimize edilmiş maliyet", f"{report.optimized_cost:,.2f} {currency}")
    m3.metric(
        "Model tahmini fark",
        f"{report.estimated_savings:,.2f} {currency}",
        f"{report.estimated_savings_percent:.1f}%",
        help="Scenario estimate versus a machine- and precedence-aware reference for the same scheduled operations; not measured bill savings.",
    )
    m4.metric("Optimize edilmiş tepe güç", f"{result.peak_power_kw:,.2f} kW")

    solver_status = (
        "Optimality proven"
        if result.is_optimal
        else "Feasible result; optimality not proven"
    )
    st.info(
        f"Solver: {result.solver_name} · {solver_status}"
        + (f" · MIP gap: {result.mip_gap:.4%}" if result.mip_gap is not None else "")
    )

    if result.late_task_count:
        st.warning(f"{result.late_task_count} scheduled operation(s) miss their soft due slot.")
    if result.total_delay_penalty:
        st.caption(f"Delay penalty (separate from electricity cost): {result.total_delay_penalty:,.2f} objective units.")

    st.subheader("Güç profili")
    st.line_chart(
        {
            "Mevcut plan (kW)": list(report.reference_load_profile_kw),
            "Optimize plan (kW)": list(result.load_profile_kw),
            "Tesis güç sınırı (kW)": [request.max_power_kw] * len(result.load_profile_kw),
        },
        y_label="Power (kW)",
        x_label="Interval index",
    )

    st.subheader("Önerilen üretim planı")
    if result.schedule:
        st.dataframe(
            [
                {
                    "Operasyon": item.name,
                    "Makine": item.machine_id or "—",
                    "Öncelik": item.priority_weight,
                    "Başlangıç aralığı": item.start_slot,
                    "Bitiş aralığı": item.end_slot_exclusive,
                    "Gecikme aralığı": item.late_slots,
                    "Enerji (kWh)": round(item.energy_kwh, 3),
                    f"Cost ({currency})": round(item.cost, 2),
                }
                for item in result.schedule
            ],
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.warning("No flexible tasks were scheduled.")
    if result.unscheduled_task_ids:
        st.warning("Unscheduled tasks: " + ", ".join(result.unscheduled_task_ids))

    payload = {
        "report_type": "modeled_scenario_comparison",
        "currency": currency,
        "solver": result.solver_name,
        "is_optimal": result.is_optimal,
        "mip_gap": result.mip_gap,
        "reference_cost": report.reference_cost,
        "optimized_cost": report.optimized_cost,
        "estimated_savings": report.estimated_savings,
        "estimated_savings_percent": report.estimated_savings_percent,
        "peak_power_kw": result.peak_power_kw,
        "load_profile_kw": list(result.load_profile_kw),
        "total_energy_kwh": result.total_energy_kwh,
        "total_delay_penalty": result.total_delay_penalty,
        "late_task_count": result.late_task_count,
        "schedule": [
            {
                "task_id": item.task_id,
                "machine_id": item.machine_id,
                "priority_weight": item.priority_weight,
                "late_slots": item.late_slots,
                "start_slot": item.start_slot,
                "end_slot_exclusive": item.end_slot_exclusive,
                "energy_kwh": item.energy_kwh,
                "cost": item.cost,
            }
            for item in result.schedule
        ],
        "unscheduled_task_ids": list(result.unscheduled_task_ids),
        "notes": [
            "Modeled estimate, not an audited or guaranteed invoice saving.",
            "Validate tariffs, taxes, demand charges, production constraints, and meter data.",
            "This application does not control physical equipment.",
        ],
    }
    st.download_button(
        "Senaryo raporunu indir (JSON)",
        json.dumps(payload, ensure_ascii=False, indent=2),
        file_name="energy-optimizer-scenario-report.json",
        mime="application/json",
    )


def run_analysis_tab() -> None:
    st.subheader("Sayaç tüketim analizi")
    st.caption(
        "Analiz için import_power_kw (toplam sayaç gücü) veya base_load_kw yükleyin; "
        "CSV/XLSX: timestamp, price_per_kwh, power column, optional production_units."
    )
    meter_file = st.file_uploader(
        "Sayaç dosyasını yükleyin",
        type=["csv", "xlsx", "xlsm"],
        key="analysis_meter",
    )
    if meter_file is None:
        st.info("Analiz için zaman damgalı bir sayaç dosyası yükleyin.")
        return
    try:
        data = read_meter_data(meter_file.name, meter_file.getvalue())
        summary = analyze_consumption(data)
    except (ValueError, ImportError) as exc:
        st.error(str(exc))
        return

    a, b, c, d = st.columns(4)
    a.metric("Toplam enerji", f"{summary.total_energy_kwh:,.2f} kWh")
    b.metric("Ölçülen maliyet", f"{summary.total_cost:,.2f}")
    c.metric("En yüksek şebeke gücü", f"{summary.peak_power_kw:,.2f} kW")
    d.metric("Yük faktörü", f"{summary.load_factor:.1%}")

    st.line_chart(
        {"Ölçülen güç (kW)": [item.base_load_kw for item in data.intervals]},
        y_label="Power (kW)",
        x_label="Interval index",
    )
    st.line_chart(
        {"Enerji birim fiyatı": [item.price_per_kwh for item in data.intervals]},
        y_label="Price per kWh",
        x_label="Interval index",
    )
    st.write(
        f"Average power: {summary.average_power_kw:.2f} kW · "
        f"Minimum power: {summary.minimum_power_kw:.2f} kW · "
        f"Interval length: {data.slot_hours:g} hours"
    )
    if summary.production_units is not None:
        st.metric(
            "Energy intensity",
            f"{summary.energy_per_production_unit:.4f} kWh / production unit",
        )
    st.write("En yüksek tüketim zamanları")
    st.dataframe(
        [{"Timestamp": value} for value in summary.peak_timestamps],
        hide_index=True,
        use_container_width=True,
    )


def run_comparison_tab() -> None:
    st.subheader("Ölçülen dönem karşılaştırması")
    st.caption(
        "Referans ve raporlama dönemleri için iki ayrı sayaç dosyası yükleyin. "
        "Üretim normalizasyonu için iki dosyada da production_units sütunu bulunmalıdır."
    )
    left, right = st.columns(2)
    with left:
        baseline_file = st.file_uploader(
            "Referans dönem (CSV/XLSX)",
            type=["csv", "xlsx", "xlsm"],
            key="baseline_meter",
        )
    with right:
        reporting_file = st.file_uploader(
            "Raporlama dönemi (CSV/XLSX)",
            type=["csv", "xlsx", "xlsm"],
            key="reporting_meter",
        )
    if baseline_file is None or reporting_file is None:
        st.info("Karşılaştırma için iki döneme ait sayaç dosyalarını yükleyin.")
        return
    try:
        baseline = read_meter_data(baseline_file.name, baseline_file.getvalue())
        reporting = read_meter_data(reporting_file.name, reporting_file.getvalue())
        comparison = compare_measured_periods(baseline, reporting)
    except (ValueError, ImportError) as exc:
        st.error(str(exc))
        return

    m1, m2, m3 = st.columns(3)
    m1.metric(
        "Enerji değişimi",
        f"{comparison.raw_energy_change_kwh:,.2f} kWh",
        f"{comparison.raw_energy_change_percent:.1f}%",
    )
    m2.metric(
        "Maliyet değişimi",
        f"{comparison.raw_cost_change:,.2f}",
        f"{comparison.raw_cost_change_percent:.1f}%",
    )
    if comparison.normalized_energy_savings_kwh is not None:
        m3.metric(
            "Üretime göre düzeltilmiş enerji farkı",
            f"{comparison.normalized_energy_savings_kwh:,.2f} kWh",
            f"{comparison.normalized_energy_savings_percent:.1f}%",
        )
        st.metric(
            "Raporlama dönemi fiyatıyla normalize maliyet tahmini",
            f"{comparison.normalized_cost_savings_estimate:,.2f}",
        )
    else:
        m3.metric("Üretime göre düzeltilmiş fark", "Not available")
    st.warning(comparison.interpretation)
    st.caption(
        "Raw cost differences are nominal and may reflect tariff changes or different "
        "period lengths. A before/after comparison alone does not prove causality."
    )


def main() -> None:
    st.set_page_config(
        page_title="Energy Optimizer",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_theme(st)
    st.markdown(
        """
        <div class="eo-topbar">
          <div class="eo-brand-mark">⚡</div>
          <div>
            <div class="eo-brand-name">Energy Optimizer</div>
            <div class="eo-brand-subtitle">Enerji ve üretim karar platformu</div>
          </div>
          <div class="eo-topbar-spacer"></div>
          <div class="eo-status"><span></span> Yerel pilot sürüm</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.title("Tesisin enerji görünümü")
    st.caption("Tüketimi anlayın, üretimi planlayın, senaryoları karşılaştırın.")

    st.info(
        "Bu sürüm yerel pilot içindir. Henüz kullanıcı girişi, müşteri verisi izolasyonu "
        "ve fiziksel ekipman kontrolü bulunmaz. Gizli müşteri verilerini herkese açık "
        "bir dağıtıma yüklemeyin.",
        icon="🔒",
    )
    optimization_tab, analysis_tab, comparison_tab = st.tabs(
        ["⚙️  Optimizasyon", "📊  Tüketim analizi", "↔️  Dönem karşılaştırması"]
    )
    with optimization_tab:
        run_optimizer_tab()
    with analysis_tab:
        run_analysis_tab()
    with comparison_tab:
        run_comparison_tab()


if __name__ == "__main__":
    main()
