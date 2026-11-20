# Energy Optimizer

**Energy Optimizer Pro** is an early-stage industrial energy analytics and production-aware scheduling product. Version 0.4.0 adds machine capacity, operation precedence, weighted priorities, and soft due-date penalties.

> **Status: pilot MVP (v0.4.0).** This is decision-support software, not a certified energy audit or guaranteed savings product. It does not control physical equipment.

## Capabilities

- Import timestamped interval meter data from UTF-8 CSV or XLSX
- Analyze kWh, cost, average and peak kW, load factor, and kWh per production unit
- Optimize flexible electrical loads under a site import-power cap
- Schedule production operations with machine exclusivity and predecessor relationships
- Prioritize critical operations and penalize soft due-date lateness
- Use SciPy/HiGHS MILP or a deterministic greedy heuristic
- Explore scenarios in a local Streamlit dashboard and export a JSON report

## Install and run

Python 3.11 or newer is required.

```bash
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -e ".[app,optimization,dev]"
streamlit run app.py
```

On macOS/Linux, use source .venv/bin/activate after creating the virtual environment.

## Production scenario fields

The existing task fields remain required: task_id, name, power_kw, duration_slots, earliest_start, and latest_start. These additional fields are optional:

| Field | Meaning |
|---|---|
| machine_id | Shared single-capacity machine/resource ID; operations cannot overlap |
| predecessors | Task IDs that must finish before this operation can start |
| due_slot | Soft deadline expressed as an exclusive finish interval |
| priority_weight | Integer 1–1000; higher values preserve more important work |
| delay_penalty_per_slot | Objective penalty per interval past due_slot |

Example operation:

```json
{
  "task_id": "drill",
  "name": "Drill housing",
  "power_kw": 8.5,
  "duration_slots": 2,
  "earliest_start": 2,
  "latest_start": 10,
  "machine_id": "CNC-01",
  "predecessors": ["cut"],
  "due_slot": 8,
  "priority_weight": 5,
  "delay_penalty_per_slot": 12.0
}
```

All times are interval indices on the same planning horizon. A due_slot of 8 means the operation should finish by the start of interval 8. It is a soft deadline; lateness is penalized, not made infeasible. Penalty units are planning-objective units and are reported separately from electricity bill cost. Priority weights are relative importance scores, not monetary values.

A machine ID represents a single-capacity resource in this release. Alternative machine routing, setup/changeover times, batch yields, labor, buffers, maintenance calendars, and quality constraints are not yet modeled.

## Meter file format

Required columns:
- timestamp: ISO-8601 timestamp with an explicit UTC offset
- price_per_kwh: price in one consistent currency per kWh
- base_load_kw: average import power for the interval, excluding modeled flexible tasks

Optional column:
- production_units: quantity produced during the interval; if present, populate every row

CSV and XLSX are supported. Timestamps must be strictly increasing and evenly spaced. Do not feed total import power into the optimizer as base load when flexible tasks are already included in that measurement.

## Optimization methods

- greedy: fast deterministic heuristic; respects supplied machine and precedence constraints but does not guarantee global optimality.
- milp: SciPy/HiGHS mixed-integer solver.
- auto: attempts MILP and falls back to greedy if SciPy is unavailable.

The MILP first maximizes the sum of scheduled task priority weights, then minimizes modeled energy cost plus due-date delay penalties. With all weights set to 1, the first objective is equivalent to maximizing the number of scheduled operations. It enforces the site power cap, single-capacity machine constraints, and declared predecessor relationships. A time-limited solve may find a feasible incumbent without proving optimality.

## Measurement limits

A modeled scenario estimate is not an audited bill saving. Metered before/after differences do not establish causality. Production mix, operating hours, weather, maintenance, tariff, and other conditions can change. The current model does not calculate every component of a Turkish electricity invoice.

## Engineering and security boundaries

This release models non-preemptive tasks with constant average power. It does not yet include forecasting, batteries, PV, alternative machine routing, setup times, labor, buffer dynamics, or process quality constraints.

The dashboard remains a local pilot with no authentication, tenant isolation, database, billing, hosted security, or physical device control. Keep integrations read-only until a separate site safety case is approved.

## Run checks

```bash
python -m compileall -q app.py src/energy_optimizer
ruff check .
pytest
```

See [the production scheduling contract](docs/production-scheduling.md), [architecture](docs/architecture.md), and [product roadmap](docs/roadmap.md) for model design, validation gates, and next milestones.

## License

MIT. See LICENSE.
