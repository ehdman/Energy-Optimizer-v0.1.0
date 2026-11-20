# Changelog

## Unreleased — non-AI infrastructure

- Added a deterministic PV self-consumption and battery dispatch simulator.
- Added battery capacity, charge/discharge power, efficiency, and state-of-charge validation.
- Added import-cap-aware dispatch, optional grid charging by explicit price ceiling, and threshold-based discharge.
- Added interval reporting for grid import, PV export, battery throughput, energy cost, optional carbon emissions, and cap violations.
- Added focused tests and operator/safety boundary documentation.
- No forecasting, AI prediction, inverter integration, or physical equipment control is included.

## 0.4.0 - Production-aware scheduling

- Added optional machine resource IDs and non-overlap constraints.
- Added predecessor relationships with unknown-reference and cycle validation.
- Added relative operation priority weights.
- Added soft due slots and separate delay penalties.
- Extended MILP and greedy solvers while retaining compatibility with existing task JSON.
- Added production-aware scenario example and test coverage.

## 0.3.0

- Added CSV/XLSX meter ingestion, consumption analysis, MILP scheduling, and measured-period comparisons.
