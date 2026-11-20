# Optimization model

## Decision variables

For each task i and feasible start slot s, binary variable x(i,s) equals 1 when task i starts at s. Binary variable u(i) marks a task as unscheduled.

## Task selection

For every task, exactly one start or unscheduled marker is selected:

sum_s x(i,s) + u(i) = 1

## Hard constraints

For every interval t, site import power is limited:

base_load(t) + sum(i,s active at t) power(i) * x(i,s) <= max_power

For each machine resource and interval, at most one operation assigned to that machine may be active.

When an operation is selected, every declared predecessor must also be selected at a start whose finish is no later than the successor start. Request validation rejects unknown predecessor IDs and dependency cycles.

## Objective

The MILP maximizes the sum of scheduled task priority weights before minimizing modeled energy cost plus explicit soft due-date delay penalties. With all weights equal to 1, maximizing scheduled priority weight is equivalent to maximizing the number of completed tasks.

The unscheduled-task penalty is derived from the sum of absolute candidate energy and delay costs, so completing one additional unit of priority weight dominates any possible cost swing in the current planning horizon. Priority weights are relative values from 1 to 1000, not monetary values. Due-date penalties are separate from reported electricity bill cost.

## Solver

SciPy's scipy.optimize.milp uses the HiGHS MILP backend. The product records the solver name, whether optimality was proven, and the reported MIP gap. A feasible time-limited result is not described as optimal.

## Greedy alternative

The deterministic greedy heuristic respects power capacity, single-capacity machines, and predecessor order. It prioritizes higher-weight tasks and then tighter windows, but it does not guarantee a globally optimal schedule.

## Current limitations

- Tasks are non-preemptive and use constant average power.
- No alternative machine routing, setup/changeover, shift calendar, batch yield, labor, buffer, maintenance, process temperature/pressure, or product-quality constraints.
- No storage, PV, demand-response, reactive power, or network flow model.
- No uncertainty, price forecasts, or robust/stochastic optimization.
- Current energy objective is not a full electricity invoice model.
