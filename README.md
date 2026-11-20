# Energy Optimizer

**Energy Optimizer Pro** is an early-stage industrial energy analytics and scheduling product. Version 0.3.0 adds timestamped CSV/XLSX meter-data import, consumption analysis, a SciPy/HiGHS MILP scheduler, and production-normalized comparisons between measured periods.

> **Status: pilot MVP (v0.3.0).** This is decision-support software, not a certified energy audit or guaranteed savings product. It does not control physical equipment. Realized savings require a site-approved measurement and verification method.

## Features

- Import timestamped interval meter data from UTF-8 CSV or XLSX
- Validate timezone-aware timestamps, regular intervals, numeric fields, and optional production quantities
- Analyze kWh, cost, average and peak kW, load factor, and kWh per production unit
- Schedule flexible loads under an import-power cap
- Use SciPy/HiGHS mixed-integer linear programming (MILP) or the greedy heuristic
- Compare measured baseline and reporting periods; normalize energy intensity when production data exists
- Explore scenarios in a local Streamlit dashboard and export a JSON report

## Install and run

Python 3.11 or newer is required.

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -e ".[app,optimization,dev]"
streamlit run app.py
```

The dashboard includes three workspaces: scenario optimization, meter analysis, and measured-period comparison.

## Meter file format

Required columns:
- `timestamp`: ISO-8601 timestamp with an explicit UTC offset, for example `2026-01-01T00:00:00+03:00`
- `price_per_kwh`: price in one consistent currency per kWh
- `base_load_kw`: measured average import power in kW for the interval

Optional column:
- `production_units`: quantity produced during the interval; if present, it must be populated on every row

Timestamps must be strictly increasing and evenly spaced. At least two rows are needed to infer interval length. CSV and XLSX are supported; XLSX reads the first worksheet. The example schema is in [examples/meter-template.csv](examples/meter-template.csv).

## Optimization methods

- `greedy`: fast deterministic heuristic; does not guarantee an optimal solution.
- `milp`: SciPy/HiGHS mixed-integer solver; install the optimization extra.
- `auto`: attempts MILP and falls back to greedy if SciPy is unavailable.

The MILP first minimizes the number of unscheduled tasks, then minimizes energy cost among schedules with the same number of scheduled tasks. It enforces the site power cap in every interval. A time-limited solve can return a feasible incumbent that is not proven optimal; inspect the solver status in the result.

## Savings and measurement limits

The scenario report compares the same successfully scheduled tasks against an earliest-allowed-start reference. It is a modeled estimate, not an invoice saving.

Measured-period comparison shows raw energy and nominal cost differences. When both files include production quantities, it also compares kWh per production unit and estimates normalized energy difference at reporting-period production. That comparison does not establish causality: weather, operating hours, product mix, maintenance, tariffs, and other conditions may change. A customer pilot should document a baseline and agreed measurement and verification method.

The current model does not fully calculate Turkish electricity invoices, including all taxes, distribution, reactive energy, demand charges, contract terms, or other tariff components.

## Run checks

```bash
python -m compileall -q app.py src/energy_optimizer
ruff check .
pytest
```

## Product and safety documents

- [Project scope](docs/project-scope.md)
- [Commercial MVP and pilot plan](docs/commercial-mvp.md)
- [Pilot security and customer data](docs/pilot-security.md)
- [Architecture](docs/architecture.md)
- [Data contract](docs/data-contract.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## Roadmap

- [x] CSV/XLSX interval meter import and validation
- [x] Consumption and production-intensity analytics
- [x] MILP scheduler and greedy fallback
- [x] Measured-period comparison with optional production normalization
- [ ] Full tariff and invoice model
- [ ] Forecasting for load, prices, and renewable generation
- [ ] API, customer accounts, tenant isolation, and secure hosted deployment
- [ ] Read-only meter/BMS integrations
- [ ] Operator-approved, safety-reviewed control integrations (separate phase)

## License

MIT. See [LICENSE](LICENSE).
