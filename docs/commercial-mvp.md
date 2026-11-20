# Commercial MVP plan

## Product definition

**Energy Optimizer Pro** is a decision-support product for industrial sites. It analyzes interval consumption, electricity prices, site power limits, and flexible operating windows to recommend lower-cost operating schedules.

The first paid use case is not autonomous plant control. It is a measurable, reviewable recommendation service for facilities with flexible loads and usable interval meter data.

## Initial ideal customer profile

Start with one industrial facility that has:
- interval meter data (15-minute or hourly, with timestamps and units);
- a known tariff structure and invoice data;
- controllable or schedulable loads such as selected pumps, compressors, chillers, water heating, thermal processes, or EV charging;
- an energy manager or operations contact who can validate operating constraints.

Do not assume every machine can be shifted. Production sequence, temperature, pressure, quality, maintenance, worker safety, and equipment warranties take precedence over a lower electricity price.

## Value proposition

1. Identify when flexible consumption can move to lower-cost periods.
2. Keep a configured site import-power limit in the proposed schedule.
3. Show a transparent reference-vs-optimized scenario comparison.
4. Export a schedule and an auditable assumptions report.
5. Later, use measured data to verify actual outcomes and distinguish energy savings from tariff arbitrage.

## MVP boundary

Included in this pilot MVP:
- local Streamlit dashboard;
- JSON scenario upload and sample scenario;
- flexible-load scheduling using the current deterministic heuristic;
- reference-vs-optimized modeled cost comparison;
- peak-power profile visualization;
- downloadable JSON result.

Not included:
- customer accounts, roles, billing, hosted multi-tenant storage, or production authentication;
- automatic utility tariff discovery;
- direct PLC, SCADA, inverter, battery, or machine control;
- certified energy audit or guaranteed savings;
- full Turkish electricity invoice calculation (taxes, distribution, reactive penalties, demand billing, contract terms).

The current dashboard is a local demonstration, not a production SaaS deployment. Never expose it publicly with real customer data until authentication, tenant isolation, transport security, retention, backup, logging, and incident response are implemented and reviewed.

## Pilot method

1. Sign a pilot agreement and define the site, data owner, permitted data, and retention period.
2. Collect at least several weeks of interval meter data, tariff details, and operating calendars.
3. Normalize data by timestamp, time zone, production volume, and relevant operating conditions.
4. Identify shiftable loads with the site engineer; document the earliest/latest start and required duration.
5. Run the optimizer in shadow mode. Recommendations are reviewed, not automatically applied.
6. Compare against a documented baseline using equivalent production and operating conditions.
7. Report modeled savings separately from measured and invoice-verified savings.
8. Obtain written customer approval before any integration or use of operational data beyond the pilot.

## Commercial models to test

- **Assessment:** fixed-fee data assessment and optimization report.
- **Pilot:** fixed-fee, time-limited shadow-mode deployment.
- **Subscription:** per-site recurring fee for dashboard, reports, and scenario planning.
- **Integration:** separately scoped fee for meter, BMS, or industrial data connectors.
- **Performance fee:** consider only after an agreed measurement and verification method is accepted by the customer and legal review is complete.

Do not publish a price list until pilot delivery cost, support burden, willingness to pay, and demonstrable customer value are known. Do not promise a fixed percentage of savings.

## Success metrics

- share of meter intervals with valid data;
- number of flexible tasks successfully scheduled;
- modeled cost difference versus the defined reference;
- measured cost difference after approved operational changes;
- peak import power (kW) and energy use (kWh);
- production-normalized energy intensity (kWh per unit produced);
- recommendation acceptance and override rate;
- customer-reported operational disruption (target: none).

## Go/no-go gates

A pilot is successful only when:
- the source data and tariff assumptions are traceable;
- no configured power or operating constraints are violated in the recommendation;
- operations staff approve the feasible schedule;
- modeled and measured outcomes are reported separately;
- the customer can reproduce the analysis from the exported inputs and report.

Only after several successful pilots should the team invest in hosted SaaS features, automated integrations, and production controls.
