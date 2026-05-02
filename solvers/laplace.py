"""
Laplace Transform Solver
Solves linear constant-coefficient ODEs via the s-domain.
Place this file at: solvers/laplace.py
"""

import sympy as sp
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional
from core.parser import ODEComponents


@dataclass
class LaplaceStep:
    step_number: int
    description: str
    equation: str
    latex: str


@dataclass
class LaplaceSolution:
    x_of_t:           Optional[sp.Expr]
    X_of_s:           Optional[sp.Expr]
    success:          bool
    message:          str
    derivation_steps: List[LaplaceStep]
    statistics:       Dict[str, float]


class LaplaceSolver:
    """
    Solve 1st / 2nd-order linear ODEs via Laplace transform.

    Pipeline
    --------
    1. Take L{ODE} using initial conditions
    2. Solve algebraically for X(s)
    3. Partial-fraction decompose X(s)
    4. Inverse-Laplace → x(t)
    """

    def __init__(self):
        self.s = sp.Symbol('s')
        self.t = sp.Symbol('t', positive=True)

    # ── public ────────────────────────────────────────────────────────

    def solve(self,
              components: ODEComponents,
              initial_conditions: Dict[str, float]) -> LaplaceSolution:

        steps: List[LaplaceStep] = []
        n = 1

        # Guard clauses
        if not components.is_linear:
            return LaplaceSolution(
                x_of_t=None, X_of_s=None, success=False,
                message="Laplace method only supports linear ODEs.",
                derivation_steps=[], statistics={}
            )
        if components.order > 2:
            return LaplaceSolution(
                x_of_t=None, X_of_s=None, success=False,
                message="Laplace solver supports up to 2nd-order ODEs.",
                derivation_steps=[], statistics={}
            )

        try:
            x0  = float(initial_conditions.get('x',  0))
            dx0 = float(initial_conditions.get('dx', 0))
            a   = float(components.coefficients.get('x2', 0))
            b   = float(components.coefficients.get('x1', 0))
            c   = float(components.coefficients.get('x0', 0))
            s   = self.s

            # Step 1 — state ODE
            steps.append(LaplaceStep(n, "Given ODE",
                components.equation,
                self._ode_latex(a, b, c, components.forcing_function)))
            n += 1

            # Step 2 — apply Laplace transform
            ic_terms    = self._ic_contribution(a, b, c, x0, dx0)
            denominator = (a*s**2 + b*s + c) if a != 0 else (b*s + c)
            steps.append(LaplaceStep(n,
                "Apply Laplace transform (with initial conditions)",
                f"({a}s² + {b}s + {c})·X(s) = F(s) + IC terms",
                self._lhs_latex(a, b, c, x0, dx0)))
            n += 1

            # Step 3 — Laplace of forcing
            F_s = self._laplace_forcing(components.forcing_function)
            steps.append(LaplaceStep(n,
                "Laplace transform of forcing function",
                f"F(s) = {F_s}",
                f"F(s) = {sp.latex(F_s)}"))
            n += 1

            # Step 4 — solve for X(s)
            X_s = sp.simplify((F_s + ic_terms) / denominator)
            steps.append(LaplaceStep(n,
                "Solve algebraically for X(s)",
                f"X(s) = {X_s}",
                f"X(s) = \\dfrac{{{sp.latex(F_s + ic_terms)}}}{{{sp.latex(denominator)}}}"))
            n += 1

            # Step 5 — partial fractions
            X_pf = sp.apart(X_s, s)
            steps.append(LaplaceStep(n,
                "Partial fraction decomposition",
                f"X(s) = {X_pf}",
                f"X(s) = {sp.latex(X_pf)}"))
            n += 1

            # Step 6 — inverse Laplace
            x_t = sp.simplify(
                sp.inverse_laplace_transform(X_pf, s, self.t)
            )
            steps.append(LaplaceStep(n,
                "Inverse Laplace transform → x(t)",
                f"x(t) = {x_t}",
                f"x(t) = {sp.latex(x_t)}"))

            stats = self._sample_stats(x_t)

            return LaplaceSolution(
                x_of_t=x_t, X_of_s=X_s,
                success=True,
                message="Laplace solution obtained successfully.",
                derivation_steps=steps,
                statistics=stats
            )

        except Exception as e:
            steps.append(LaplaceStep(n, "Solver error", str(e), f"\\text{{Error: {e}}}"))
            return LaplaceSolution(
                x_of_t=None, X_of_s=None,
                success=False, message=f"Laplace solver failed: {e}",
                derivation_steps=steps, statistics={}
            )

    # ── private helpers ───────────────────────────────────────────────

    def _laplace_forcing(self, forcing_str):
        s = self.s
        if not forcing_str or forcing_str == '0':
            return sp.Integer(0)

        import re
        f = forcing_str.strip().lower()

        # Common closed-form pairs
        if f == 'cos(t)':   return s / (s**2 + 1)
        if f == 'sin(t)':   return sp.Integer(1) / (s**2 + 1)

        m = re.match(r'cos\((\d*\.?\d+)\*?t\)', f)
        if m:
            w = float(m.group(1)); return s / (s**2 + w**2)

        m = re.match(r'sin\((\d*\.?\d+)\*?t\)', f)
        if m:
            w = float(m.group(1)); return w / (s**2 + w**2)

        m = re.match(r'exp\((-?\d*\.?\d+)\*?t\)', f)
        if m:
            a = float(m.group(1)); return sp.Integer(1) / (s - a)

        # Fallback: use SymPy's Laplace transform
        try:
            t_sym = self.t
            expr  = sp.sympify(forcing_str,
                               locals={'t': t_sym, 'sin': sp.sin,
                                       'cos': sp.cos, 'exp': sp.exp})
            return sp.laplace_transform(expr, t_sym, s, noconds=True)
        except Exception:
            return sp.Integer(0)

    def _ic_contribution(self, a, b, c, x0, dx0):
        s = self.s
        if a != 0:
            return a * (s * x0 + dx0) + b * x0
        elif b != 0:
            return b * x0
        return sp.Integer(0)

    def _ode_latex(self, a, b, c, forcing):
        parts = []
        if a != 0: parts.append(f"{a}\\ddot{{x}}")
        if b != 0: parts.append(f"{b}\\dot{{x}}")
        if c != 0: parts.append(f"{c}x")
        lhs = " + ".join(parts) or "0"
        rhs = sp.latex(sp.sympify(forcing, locals={'t': self.t, 'sin': sp.sin, 'cos': sp.cos, 'exp': sp.exp})) if forcing else "0"
        return f"{lhs} = {rhs}"

    def _lhs_latex(self, a, b, c, x0, dx0):
        s     = self.s
        coeff = a*s**2 + b*s + c if a != 0 else b*s + c
        ic    = self._ic_contribution(a, b, c, x0, dx0)
        return (f"\\left({sp.latex(coeff)}\\right) X(s) "
                f"= F(s) + {sp.latex(ic)}")

    def _sample_stats(self, x_t_expr):
        try:
            t_vals = np.linspace(0, 50, 500)
            f      = sp.lambdify(self.t, x_t_expr, modules=['numpy'])
            x_vals = np.array([float(np.real(f(ti))) for ti in t_vals])
            x_vals = x_vals[np.isfinite(x_vals)]
            if len(x_vals) == 0:
                return {}
            return {
                'x_final': float(x_vals[-1]),
                'x_max':   float(np.max(x_vals)),
                'x_min':   float(np.min(x_vals)),
                'x_mean':  float(np.mean(x_vals)),
                'x_std':   float(np.std(x_vals)),
            }
        except Exception:
            return {}