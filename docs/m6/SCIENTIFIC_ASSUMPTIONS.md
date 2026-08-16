# M6 Scientific Assumptions & Model Fidelity

This document explicitly defines the physical assumptions, simplifications, and limitations of the M6 Lunar Hazard Mapper planning prototype.

## Purpose
The M6 Planner is designed for **local lunar landing-site reachability and comparative descent planning**. It is explicitly **not** intended for flight certification, full orbital propagation, or operational guidance.

## Physics & Dynamics
*   **Gravity:** Constant over the local simulation region ($g = 1.62 \text{ m/s}^2$).
*   **Dynamics:** 3-DOF translational dynamics. Full 6-DOF rigid body attitude dynamics are excluded.
*   **Coordinate System:** Local Cartesian frame where $X = \text{East}$, $Y = \text{North}$, and $Z = \text{Up}$ relative to a selected landing region reference point. Selenographic mapping (Lat/Lon/Altitude) is excluded from the inner simulation loop.

## Guidance & Control
*   **Controller:** A baseline Proportional-Derivative (PD) translational controller is used to generate deterministic, physically constrained candidate descent trajectories.
*   **Optimization:** The controller does not implement full fuel-optimal guidance (e.g. Apollo E-Guidance) or optimal control solvers.
*   **Thrust:** Bounded by `maxThrust` and constrained geometrically by `maxTiltAngle` to prevent physically impossible instantaneous lateral acceleration.

## $\Delta v$ Estimation
*   **Available $\Delta v$:** Extracted from the provided `LanderProfile.deltaVBudget`.
*   **Required $\Delta v$:** Uses a simplified local kinematic maneuver estimate (accelerate to midpoint, decelerate to target) plus vertical gravity losses. It does not solve Lambert's problem, which applies to two-body orbital transfer rather than terminal powered descent.

## Terrain & Collision Detection
*   **Terrain Data:** The M3 DEM is treated as absolute terrain truth input. M6 does not recompute slope/crater/boulder feasibility; it defers to M5.
*   **Ground Detection:** Handled dynamically via a `TerrainProvider` adapter during numerical integration, ensuring realistic ground-collision triggering instead of assuming a perfectly flat plane at $Z = 0$.

## Uncertainty Simulation
*   **Monte Carlo Perturbations:** Gaussian noise is injected into the initial state (position, altitude, velocity) using configurable standard deviations.
