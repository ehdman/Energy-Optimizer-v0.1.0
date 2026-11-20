# Production-aware scheduling (v0.4.0)

## Purpose

This module extends flexible-load scheduling into a small, explicit production-operation model. It is intended for shadow-mode planning and engineer-reviewed scenarios, not autonomous plant control.

## Operation contract

Each operation uses the existing task fields plus optional metadata:

- machine_id: a single-capacity resource identifier. Tasks sharing this exact ID cannot overlap.
- predecessors: IDs of all direct operations that must finish before this operation starts.
- priority_weight: integer 1–1000. Larger values give the operation greater protection from being left unscheduled.
- due_slot: soft finish deadline, represented as an exclusive interval index.
- delay_penalty_per_slot: non-negative objective penalty for each interval by which the operation finishes after due_slot.

All time values are interval indices on the same horizon. Task duration is a positive integer number of intervals. Power is constant average kW throughout the task in this release.

## Objective and constraints

The MILP maximizes the sum of scheduled priority weights before minimizing the combined modeled energy cost and due-date penalty. With uniform priority 1, this maximizes the number of scheduled operations before optimizing energy cost.

Hard constraints:
- site import power does not exceed configured capacity;
- a single-capacity machine cannot run two operations at once;
- all declared predecessors must be scheduled and must finish before the successor starts;
- every operation is either assigned exactly one feasible start or marked unscheduled.

Soft constraint:
- due-slot lateness is penalized, but a late operation may still be scheduled.

Delay-penalty units are deliberately separate from electricity tariff units and are not added to the reported bill cost. Priority weights are relative business preferences, not money.

## Limitations and required site validation

A machine_id is an exclusive resource, not a machine-selection decision. This model does not choose among alternative machines or represent parallel identical machines. It also omits setup/changeover times, product routes, batch yields, labor, buffers, inventory, shift calendars, maintenance, process limits, quality, and variable power profiles. Those should be added only with validated plant data and tests.

Do not infer machine or process constraints from energy data alone. Obtain operation sequences and resource rules from a responsible production/industrial engineer. Keep the tool in shadow mode and have operators approve recommendations.
