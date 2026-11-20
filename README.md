# Energy Optimizer

**Energy Optimizer Pro** is an early-stage, factory-focused energy scheduling and decision-support product. It analyzes energy prices, a fixed site load profile, flexible operating tasks, and a site power limit to recommend lower-cost schedules.

> **Status: pilot MVP (v0.2.0).** The current scheduling engine is a deterministic heuristic, not a globally optimal solver. The dashboard produces modeled scenario comparisons, not audited savings or guaranteed bill reductions. It does not control physical equipment.

## What is included

- Python scheduling core with input validation
- Power-cap-aware scheduling of non-preemptive flexible loads
- Reference-vs-optimized cost comparison for the same successfully scheduled work
- Peak-power profile comparison
- Local Streamlit dashboard with JSON scenario upload
- Downloadable JSON optimization report
- Pilot scope, data contract, architecture, commercial plan, and pilot-security documentation
- Automated tests and GitHub Actions CI

## Run the local pilot dashboard

Python 3.11 or newer is required.

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -e ".[app,dev]"
streamlit run app.py
```

The dashboard opens in your browser and loads the sample scenario by default. Upload a JSON scenario to test your own modeled assumptions. The schema is demonstrated in [examples/day_ahead.json](examples/day_ahead.json).

## Run tests and the command-line example

```bash
pip install -e ".[dev]"
python examples/run_example.py
pytest
ruff check .
```

## How the optimizer works

1. The site supplies a price series, fixed/base load series, slot length, and maximum import-power limit.
2. Each flexible task defines its power, continuous runtime, and earliest/latest allowed start.
3. The engine evaluates feasible start windows and places tasks into lower-cost periods without exceeding the configured power cap.
4. The reporting module compares the optimized schedule against an earliest-allowed-start reference for the same tasks that were successfully scheduled.

The comparison is a model estimate. It may not equal an electricity invoice because the current MVP does not fully model taxes, distribution charges, reactive energy, demand charges, contract terms, production volume, weather, or operational constraints. Unscheduled tasks are excluded from both sides of the savings comparison so omitted work is not incorrectly reported as savings.

## Project structure

```text
app.py                          # Local pilot dashboard
src/energy_optimizer/            # Domain models, heuristic, and reporting
examples/                       # Sample scenario and meter-data template
tests/                           # Automated tests
docs/                             # Product scope, architecture, and pilot plan
.github/workflows/               # Continuous integration
```

## Product and pilot documents

- [Project scope](docs/project-scope.md)
- [Commercial MVP and pilot plan](docs/commercial-mvp.md)
- [Pilot security and customer data](docs/pilot-security.md)
- [Architecture](docs/architecture.md)
- [Data contract](docs/data-contract.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)

## Roadmap

- [x] Core flexible-load scheduling heuristic
- [x] Transparent reference-vs-optimized scenario report
- [x] Local pilot dashboard and JSON scenario upload
- [x] Downloadable optimization report
- [ ] Validated CSV/Excel meter-data ingestion with timestamps and time zones
- [ ] Full tariff and invoice model
- [ ] Exact/near-optimal MILP or CP-SAT solver and benchmark suite
- [ ] Forecasting for load, prices, and renewable generation
- [ ] Customer accounts, role-based access, tenant isolation, and secure hosted deployment
- [ ] Read-only meter/BMS integrations
- [ ] Operator-approved, safety-reviewed control integrations (separate project phase)

## Commercial positioning

The first product offer is a factory energy optimization pilot: analyze customer-authorized interval data, model flexible loads, produce an auditable recommendation, and measure the outcome under agreed conditions. Do not promise a fixed savings percentage. See [docs/commercial-mvp.md](docs/commercial-mvp.md).

## Safety and data handling

This version is a local decision-support demo. It has no customer authentication, multi-tenant database, production hosting controls, or machine-control integration. Do not upload confidential customer data to an internet-accessible deployment. Review [docs/pilot-security.md](docs/pilot-security.md) before any hosted pilot.

## License

MIT. See [LICENSE](LICENSE).
