# Optimization model

## Decision variables

For each task i and valid start slot s, define binary variable x(i,s). It equals 1 when task i starts at s. Define binary variable u(i) for a task that is not scheduled.

## Task selection

For every task, exactly one start or unscheduled marker is selected:

sum_s x(i,s) + u(i) = 1

## Site power constraint

For every interval t:

base_load(t) + sum(i,s active at t) power(i) * x(i,s) <= max_power

## Objective

The current model minimizes the number of unscheduled tasks first. A penalty larger than twice the sum of absolute candidate task costs is applied to each unassigned task. Among schedules with the same number of completed tasks, the model minimizes energy cost.

This lexicographic approximation is finite and derived from the input costs. If future business requirements assign different priority or value to tasks, explicit task priorities or weighted service levels should replace the uniform task-count objective.

## Solver

SciPy's scipy.optimize.milp uses the HiGHS MILP backend. The product records the solver name, whether optimality was proven, and the reported MIP gap. A feasible time-limited result is not described as optimal.

## Current limitations

- Tasks are non-preemptive and use constant power.
- No precedence, setup time, minimum off-time, ramping, temperature, pressure, or product quality constraints.
- No storage, PV, demand-response, reactive power, or network flow model.
- No uncertainty, price forecasts, or robust/stochastic optimization.
- Current model objective is energy tariff cost plus task completion priority; it is not a full electricity invoice optimizer.
