"""
Euler Method Solver (Educational)
Implements Forward Euler and Improved Euler (Heun's Method)
Place this file at: solvers/euler.py
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, List
from core.parser import ODEComponents, ODEParser


@dataclass
class EulerSolution:
    """Solution produced by Euler methods"""
    t: np.ndarray
    y: np.ndarray                  # shape: (n_states, n_timepoints)
    success: bool
    message: str
    method: str                    # 'Forward Euler' or 'Improved Euler (Heun)'
    step_size: float
    statistics: Dict[str, float]
    steps_table: List[Dict]        # First 10 steps for educational display


class EulerSolver:
    """
    Euler method ODE solver for educational purposes.

    Forward Euler (1st order):
        y_{n+1} = y_n + h * f(t_n, y_n)

    Improved Euler / Heun's Method (2nd order, more accurate):
        k1 = f(t_n, y_n)
        k2 = f(t_n + h, y_n + h*k1)
        y_{n+1} = y_n + (h/2) * (k1 + k2)
    """

    def __init__(self):
        self.parser = ODEParser()

    def solve(self,
              components: ODEComponents,
              initial_conditions: Dict[str, float],
              time_span: Tuple[float, float] = (0, 50),
              n_steps: int = 1000,
              variant: str = 'improved') -> EulerSolution:
        """
        Solve ODE using an Euler method.

        Args:
            components        : Parsed ODE from ODEParser
            initial_conditions: {'x': x0, 'dx': dx0}
            time_span         : (t_start, t_end)
            n_steps           : Number of integration steps
            variant           : 'forward' or 'improved'
        """
        system_func, y0 = self.parser.to_first_order_system(
            components, initial_conditions
        )

        t0, tf = time_span
        h = (tf - t0) / n_steps
        t_arr = np.linspace(t0, tf, n_steps + 1)
        y_arr = np.zeros((len(y0), n_steps + 1))
        y_arr[:, 0] = y0

        try:
            if variant == 'forward':
                y_arr, steps_table = self._forward_euler(
                    system_func, t_arr, y_arr, h
                )
                method_name = 'Forward Euler'
            else:
                y_arr, steps_table = self._improved_euler(
                    system_func, t_arr, y_arr, h
                )
                method_name = "Improved Euler (Heun's)"

            stats = self._compute_statistics(t_arr, y_arr)

            return EulerSolution(
                t=t_arr, y=y_arr,
                success=True,
                message="Integration completed successfully.",
                method=method_name,
                step_size=h,
                statistics=stats,
                steps_table=steps_table
            )

        except Exception as e:
            return EulerSolution(
                t=np.array([]), y=np.array([[]]),
                success=False, message=str(e),
                method=variant, step_size=h,
                statistics={}, steps_table=[]
            )

    # ── core loops ────────────────────────────────────────────────────

    def _forward_euler(self, f, t_arr, y_arr, h):
        steps_table = []
        for n in range(len(t_arr) - 1):
            tn, yn = t_arr[n], y_arr[:, n]
            slope  = np.array(f(tn, yn), dtype=float)
            y_next = yn + h * slope
            y_arr[:, n + 1] = y_next
            if n < 10:
                steps_table.append({
                    'step_number': n,
                    'n': n,
                    't_n':      round(float(tn),       6),
                    'x_n':      round(float(yn[0]),    6),
                    'f(t,y)':   round(float(slope[0]), 6),
                    'x_{n+1}':  round(float(y_next[0]),6),
                })
        return y_arr, steps_table

    def _improved_euler(self, f, t_arr, y_arr, h):
        steps_table = []
        for n in range(len(t_arr) - 1):
            tn, yn = t_arr[n], y_arr[:, n]
            k1     = np.array(f(tn,     yn),        dtype=float)
            k2     = np.array(f(tn + h, yn + h*k1), dtype=float)
            y_next = yn + (h / 2) * (k1 + k2)
            y_arr[:, n + 1] = y_next
            if n < 10:
                steps_table.append({
                    'step_number': n,
                    'n':        n,
                    't_n':      round(float(tn),       6),
                    'x_n':      round(float(yn[0]),    6),
                    'k1':       round(float(k1[0]),    6),
                    'k2':       round(float(k2[0]),    6),
                    'x_{n+1}':  round(float(y_next[0]),6),
                })
        return y_arr, steps_table

    def _compute_statistics(self, t, y):
        x = y[0]
        stats = {
            'x_final': float(x[-1]),
            'x_max':   float(np.max(x)),
            'x_min':   float(np.min(x)),
            'x_mean':  float(np.mean(x)),
            'x_std':   float(np.std(x)),
        }
        if y.shape[0] > 1:
            v = y[1]
            stats.update({'v_final': float(v[-1]),
                          'v_max':   float(np.max(v)),
                          'v_min':   float(np.min(v))})
        return stats