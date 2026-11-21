# Product and engineering roadmap

The roadmap is organized around measurable pilot readiness, not feature count. Each phase has an exit gate. New optimization terms are added only when the site can supply trustworthy data and an operator can validate the assumptions.

## v0.4.0 — Production-aware scheduling foundation

**Status: implemented on `main`; automated CI checks pass.**

- Machine exclusivity constraints.
- Predecessor/successor relationships and dependency-cycle validation.
- Relative operation priorities.
- Soft due slots with a separate delay penalty.
- MILP and a constraint-respecting greedy alternative.
- Sample manufacturing-line scenario and explicit scope documentation.
- Bounded MILP model construction to prevent oversized scenarios from exhausting the pilot process.

**Exit gate:** CI green; legacy v0.3 scenarios still work; tests prove machine, precedence, power-cap, and priority behavior.

## v0.5.0 — Real production planning

- Work orders, products, batches, quantities, and routing steps.
- Alternative machine assignment and parallel machine capacity.
- Setup/changeover matrices, sequence-dependent cleaning and transition times.
- Shift calendars, maintenance windows, planned downtime, and operator availability.
- Material/buffer constraints and delivery commitments.
- Variable power profiles where measured data supports them.

**Exit gate:** a site engineer signs off the resource/process model; a historical replay reproduces known schedules; infeasibility reports identify the limiting constraints. Do not infer process sequences from meter signals.

## v0.6.0 — Site energy asset simulation and scenario analysis

- PV generation, battery state of charge, efficiency, reserve, and degradation.
- Demand/contract power and full tariff components when supplied by the customer and verified against invoices.
- Carbon intensity only from traceable time- and region-specific factors.
- Pareto comparisons for energy cost, delivery delay, peak power, carbon, and asset wear.
- Scenario-based digital twin with explicit assumptions and sensitivity analysis.

**Exit gate:** conservation and equipment constraints pass property tests; model outputs reconcile to site data; investment claims are sensitivity-tested rather than guaranteed.

## v0.7.0 — Secure data platform and read-only integrations

- Authenticated API, role-based authorization, tenant isolation, and customer-specific retention/deletion.
- Database migrations, backups, audit logs, observability, and reproducible report versions.
- Read-only meter, BMS, and approved OT data ingestion through isolated gateways.
- Threat modeling, dependency scanning, incident response, and security review.

**Exit gate:** security review and customer data-protection terms completed; integration runs read-only in shadow mode; no internet-exposed dashboard with customer data.

## v1.0.0 — Commercially deployable product

- Repeatable onboarding, site configuration, permissions, support and service-level process.
- Reproducible pilot evidence and an agreed measurement-and-verification protocol.
- Deployment, backup/restore, monitoring, release, and rollback procedures.
- Pricing and commercial terms based on pilot economics and support cost.

**Exit gate:** at least one customer pilot validated by operations and energy stakeholders; the product demonstrates repeatable value without violating plant constraints.

## Engineering principles

1. Safety, process quality, and committed production constraints are hard constraints; they are not traded away for a lower energy bill.
2. Distinguish measured data, deterministic model estimates, and verified savings in every report.
3. Prefer interpretable constraints and traceable data contracts over opaque scoring.
4. Re-optimize in a bounded rolling horizon; never allow unbounded model growth.
5. Start OT integrations read-only. Any future write path requires separate authorization, safety engineering, operator approval, fail-safe behavior, and rollback.
6. Do not claim a saving percentage, carbon reduction, or payback before a customer-specific baseline and assumptions are reviewed.
