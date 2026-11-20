# Measurement and verification notes

## Why two different savings numbers exist

1. **Modeled scenario difference** compares an optimizer-generated schedule with an explicitly defined reference schedule. It estimates what the modeled flexible tasks could cost under the supplied tariffs.
2. **Measured period difference** compares actual meter files for a baseline and reporting period. It reports nominal kWh and tariff-cost changes.
3. **Production-normalized intensity** compares kWh per production unit when both periods provide a comparable production measure. It helps control for a change in output volume but does not by itself prove that the optimizer caused the difference.

These figures must be labeled separately in any customer-facing report.

## Minimum pilot data

- timestamped interval active import power;
- interval tariff or a documented tariff mapping;
- consistent interval duration and time zone;
- production quantity per interval or per shift, where meaningful;
- operating calendar and known outages;
- notes on product mix, weather-sensitive processes, maintenance, and process changes.

## Suggested comparison method

1. Agree and freeze a baseline period before recommendations are applied.
2. Define the reporting period and any exclusions before reviewing the outcome.
3. Check meter completeness, timestamps, units, tariff mapping, and production totals.
4. Compare total kWh, peak kW, nominal energy cost, and kWh per unit.
5. Explain material differences in output volume, product mix, operating hours, weather, maintenance, and tariffs.
6. If conditions differ materially, have an energy professional agree on a suitable adjustment method before describing savings as verified.
7. Retain source files, calculations, assumptions, and approval history so the customer can reproduce the report.

## Product boundary

The current comparison utility is a transparent screening analysis, not an IPMVP-compliant measurement and verification service or formal energy audit. It does not calculate every invoice component or model all independent variables. Avoid performance-fee contracts and guaranteed savings claims until a customer-specific measurement plan and legal review are complete.
