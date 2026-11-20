# Commercial MVP and pilot plan

## Product definition

**Energy Optimizer Pro** is a decision-support product for industrial sites. It analyzes timestamped interval meter data, tariffs, production quantities when available, site power limits, and flexible operating windows to recommend lower-cost schedules.

## v0.3.0 pilot capabilities

- CSV/XLSX meter import with timestamp, interval, unit, and numeric validation
- Consumption analysis: kWh, nominal tariff cost, average/peak kW, load factor
- Production-normalized kWh per production unit when comparable production data exists
- MILP scheduling through SciPy/HiGHS, with a greedy method for quick comparison
- Modeled scenario savings estimate against an explicit earliest-start reference
- Before/after metered-period comparison; raw nominal changes and normalized intensity are reported separately
- Local Streamlit demonstration and downloadable scenario report

## Initial ideal customer

Start with one industrial site that has:
- interval meter data (15-minute or hourly, timestamped and timezone-aware);
- known tariff and invoice information;
- flexible loads such as selected pumps, compressors, chillers, thermal storage, water heating, or EV charging;
- a plant engineer or operations contact who can validate process constraints;
- production-volume data if the customer wants intensity-normalized comparisons.

## Value proposition

1. Identify shiftable consumption periods.
2. Enforce a configured import-power cap in candidate schedules.
3. Compare alternative schedules transparently.
4. Reveal measured consumption, peak demand, and production-normalized energy intensity.
5. Establish a baseline and measurement method before claiming realized savings.

## Pilot boundary

The dashboard is a local pilot, not a production SaaS deployment. It has no customer login, tenant isolation, database, billing, hosted operations, or industrial control. Do not expose it publicly or use confidential customer files until access control, privacy, retention, transport security, backup, logging, incident response, and customer contracts are implemented and reviewed.

## Pilot workflow

1. Agree on site scope, data owner, permitted use, access, retention, and deletion terms.
2. Collect several weeks of timestamped interval data, tariff details, and operating/production calendars.
3. Keep import_power_kw (total measured site power) distinct from base_load_kw (residual load excluding flexible tasks).
4. Identify shiftable tasks with the site engineer. Record runtime, allowed start windows, power, and process dependencies.
5. Run recommendations in shadow mode; operations staff review and approve.
6. Compare measured periods with production normalization where possible. Record tariff, weather, shift, maintenance, product-mix, and operating-hour differences.
7. Report modeled schedule benefit separately from measured before/after changes. Do not claim causality unless an agreed measurement and verification method supports it.
8. Only after written approval consider read-only BMS/meter integration. Control integration requires a separate safety case.

## Commercial models to test

- fixed-fee data assessment and optimization report;
- time-limited fixed-fee shadow-mode pilot;
- per-site recurring subscription after secure hosted deployment;
- separately scoped data integration;
- performance fee only after an agreed, independently reviewable measurement method and legal review.

Do not publish a price list or promise a fixed savings percentage before pilot economics and support costs are known.

## Success metrics

- valid meter interval coverage;
- energy (kWh), average and peak demand (kW), and load factor;
- percentage of flexible tasks scheduled within their windows;
- modeled scenario cost difference;
- measured kWh per production unit;
- customer-approved measured savings method;
- recommendation acceptance/override rate;
- operational disruptions (target: none).

## Go/no-go gates

- source data, tariff, units, timestamps, and assumptions are traceable;
- no configured power or operating constraints are violated;
- operations staff approve proposed schedules;
- modeled and measured values are labeled separately;
- pilot findings can be reproduced from source files and exported reports;
- privacy and security terms are agreed before customer data is uploaded.
