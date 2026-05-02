"""
utils/verifier.py
─────────────────
ODEVerifier — runs 6 independent checks on every computed ODE solution
and returns a VerificationReport dataclass with per-source details.

Checks
------
1. Known Analytical Library
2. WolframAlpha API (optional)
3. Energy Conservation
4. Cross-Method Agreement (RK45 reference)
5. ODE Residual Check
6. Initial Condition Satisfaction
"""

from __future__ import annotations

import re
import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import numpy as np
from scipy.integrate import solve_ivp


# ─────────────────────────────────────────────────────────────────────────────
# Dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class VerificationSource:
    name: str
    status: str          # "pass" | "fail" | "skip" | "error"
    message: str
    max_error: Optional[float] = None
    mean_error: Optional[float] = None
    confidence: Optional[float] = None   # 0-100
    reference_t: Optional[list] = None
    reference_y: Optional[list] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationReport:
    sources: List[VerificationSource]
    overall_status: str   # "verified" | "warning" | "failed" | "partial"
    overall_confidence: float
    summary: str
    compute_ms: float


# ─────────────────────────────────────────────────────────────────────────────
# Helper: extract linear 2nd-order coefficients from components
# ─────────────────────────────────────────────────────────────────────────────

def _get_coeffs(components) -> Optional[Dict[str, float]]:
    """
    Try to read {a, b, c} from components.coefficients where the ODE is
        a*x'' + b*x' + c*x = f(t)
    Returns None if not available / non-linear.
    """
    try:
        if not components.is_linear:
            return None
        coeffs = components.coefficients
        a = float(coeffs.get("x2", coeffs.get("a", 1.0)))
        b = float(coeffs.get("x1", coeffs.get("b", 0.0)))
        c = float(coeffs.get("x0", coeffs.get("c", 0.0)))
        return {"a": a, "b": b, "c": c}
    except Exception:
        return None


def _get_forcing(components) -> Optional[str]:
    """Return the forcing string or None for homogeneous."""
    try:
        if components.is_homogeneous:
            return None
        return str(components.forcing_function)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Check 1 — Known Analytical Library
# ─────────────────────────────────────────────────────────────────────────────

def _check_analytical(components, result: Dict, ic: Dict) -> VerificationSource:
    """
    Match equation against 6 built-in families and compare exact solution.
    Families:
      1. Simple Harmonic:    x'' + ω²x = 0        (b=0, c>0, homog.)
      2. Underdamped:        x'' + bx' + cx = 0   (b² - 4c < 0)
      3. Critically Damped:  x'' + bx' + cx = 0   (b² - 4c = 0)
      4. Overdamped:         x'' + bx' + cx = 0   (b² - 4c > 0)
      5. First-order decay:  x' + kx = 0           (1st order, b<0?)
      6. First-order growth: x' + kx = 0           (1st order, b>0?)
    """
    name = "Known Analytical Library"

    try:
        coeffs = _get_coeffs(components)
        x0 = float(ic.get("x", 1.0))
        dx0 = float(ic.get("dx", 0.0))
        t_arr = np.array(result["t"])
        y_arr = np.array(result["y"])
        x_num = y_arr[0]   # position row

        # ── First-order ODEs ──────────────────────────────────────────────
        if components.order == 1 and components.is_homogeneous and components.is_linear:
            try:
                k_val = float(components.coefficients.get("x", 0.0))
                # x' + kx = 0  →  x(t) = x0 * exp(-k*t)
                x_exact = x0 * np.exp(-k_val * t_arr)
                family = "First-order decay" if k_val > 0 else "First-order growth"
                formula = f"x(t) = {x0:.4f} * exp({-k_val:.4f} * t)"
            except Exception:
                return VerificationSource(name=name, status="skip",
                                           message="1st-order coefficients not extractable.",
                                           details={})

        elif coeffs is None or components.order != 2:
            return VerificationSource(name=name, status="skip",
                                       message="Equation not 2nd-order linear homogeneous — no built-in formula.",
                                       details={})

        else:
            a, b, c = coeffs["a"], coeffs["b"], coeffs["c"]

            # Normalise to x'' + (b/a)x' + (c/a)x = 0
            B = b / a
            C = c / a
            disc = B * B - 4 * C

            if not components.is_homogeneous:
                return VerificationSource(name=name, status="skip",
                                           message="Forcing term present — exact formula not in built-in library.",
                                           details={})

            if abs(B) < 1e-9 and C > 0:
                # 1. Simple Harmonic
                omega = math.sqrt(C)
                # x(t) = x0*cos(ωt) + (dx0/ω)*sin(ωt)
                x_exact = x0 * np.cos(omega * t_arr) + (dx0 / omega) * np.sin(omega * t_arr)
                family = "Simple Harmonic Oscillator"
                formula = f"x(t) = {x0:.4f}·cos({omega:.4f}t) + {dx0/omega:.4f}·sin({omega:.4f}t)"

            elif disc < -1e-9:
                # 2. Underdamped
                alpha = B / 2
                omega_d = math.sqrt(-disc) / 2
                A1 = x0
                A2 = (dx0 + alpha * x0) / omega_d
                x_exact = np.exp(-alpha * t_arr) * (A1 * np.cos(omega_d * t_arr) + A2 * np.sin(omega_d * t_arr))
                family = "Underdamped Oscillator"
                formula = f"x(t) = e^(-{alpha:.4f}t) · [{A1:.4f}cos({omega_d:.4f}t) + {A2:.4f}sin({omega_d:.4f}t)]"

            elif abs(disc) <= 1e-9:
                # 3. Critically Damped
                r = -B / 2
                C1 = x0
                C2 = dx0 - r * x0
                x_exact = np.exp(r * t_arr) * (C1 + C2 * t_arr)
                family = "Critically Damped Oscillator"
                formula = f"x(t) = e^({r:.4f}t) · ({C1:.4f} + {C2:.4f}·t)"

            else:
                # 4. Overdamped
                sqrt_disc = math.sqrt(disc)
                r1 = (-B + sqrt_disc) / 2
                r2 = (-B - sqrt_disc) / 2
                if abs(r1 - r2) < 1e-12:
                    r1 += 1e-12
                C1 = (dx0 - r2 * x0) / (r1 - r2)
                C2 = x0 - C1
                x_exact = C1 * np.exp(r1 * t_arr) + C2 * np.exp(r2 * t_arr)
                family = "Overdamped Oscillator"
                formula = f"x(t) = {C1:.4f}·e^({r1:.4f}t) + {C2:.4f}·e^({r2:.4f}t)"

        # ── Error metrics ─────────────────────────────────────────────────
        err = np.abs(x_num - x_exact)
        max_err = float(np.max(err))
        mean_err = float(np.mean(err))
        scale = max(float(np.max(np.abs(x_exact))), 1e-10)
        conf = max(0.0, (1.0 - mean_err / scale) * 100.0)

        threshold = 0.05 * scale
        status = "pass" if mean_err < threshold else "fail"
        msg = (f"{family} — mean error {mean_err:.3e}, max error {max_err:.3e}. "
               f"Confidence {conf:.1f}%.")

        return VerificationSource(
            name=name,
            status=status,
            message=msg,
            max_error=max_err,
            mean_error=mean_err,
            confidence=conf,
            reference_t=t_arr.tolist(),
            reference_y=x_exact.tolist(),
            details={"family": family, "formula": formula},
        )

    except Exception as exc:
        return VerificationSource(name=name, status="error",
                                   message=f"Exception: {exc}", details={})


# ─────────────────────────────────────────────────────────────────────────────
# Check 2 — WolframAlpha API
# ─────────────────────────────────────────────────────────────────────────────

def _check_wolfram(components, result: Dict, ic: Dict,
                   time_span, wolfram_app_id: Optional[str]) -> VerificationSource:
    """
    Strategy: use our own SymPy solver to get the reference solution expression,
    then ask Wolfram to evaluate that expression numerically at 5 sample points
    via the Short Answers API (/v1/result).  This avoids asking Wolfram to solve
    the ODE (whose plaintext output is truncated and unparseable for complex ODEs)
    and instead uses Wolfram purely as an independent numeric evaluator.

    Flow:
      1. Solve ODE symbolically with SymPy → get x(t) expression
      2. Convert expression to a Wolfram-readable string
      3. For each sample t, ask: "N[<expr>, {t, <val>}]" via Short Answers API
      4. Compare Wolfram's number against our numerical solver's value
    """
    name = "WolframAlpha API"

    if not wolfram_app_id:
        return VerificationSource(name=name, status="skip",
                                   message="No WolframAlpha App ID provided. Skipped.",
                                   details={})
    try:
        import requests
        import sympy as sp

        t_arr = np.array(result["t"])
        y_arr = np.array(result["y"])
        x_num = y_arr[0]

        t0, t_end = float(time_span[0]), float(time_span[1])

        # ── Step 1: get fully-determined reference solution from SymPy ──────────
        # We call dsolve with ics= so C1/C2 are eliminated. This gives a numeric
        # expression we can evaluate at any t — no free constants remaining.
        try:
            t_sym = sp.Symbol("t", positive=True)
            x_fn  = sp.Function("x")
            x0_val  = float(ic.get("x",  1.0))
            dx0_val = float(ic.get("dx", 0.0))

            a = float(components.coefficients.get("x2", 0))
            b = float(components.coefficients.get("x1", 0))
            c_coef = float(components.coefficients.get("x0", 0))
            forcing_str = str(components.forcing_function or "0")
            forcing_sym = sp.sympify(forcing_str,
                                     locals={"t": t_sym, "sin": sp.sin,
                                             "cos": sp.cos, "exp": sp.exp})

            ode_eq = sp.Eq(
                sp.sympify(a) * x_fn(t_sym).diff(t_sym, 2) +
                sp.sympify(b) * x_fn(t_sym).diff(t_sym) +
                sp.sympify(c_coef) * x_fn(t_sym),
                forcing_sym
            )
            ics = {x_fn(0): x0_val, x_fn(t_sym).diff(t_sym).subs(t_sym, 0): dx0_val}
            dsolve_result = sp.dsolve(ode_eq, x_fn(t_sym), ics=ics)
            ref_expr = sp.simplify(dsolve_result.rhs)

            if ref_expr is None:
                raise ValueError("dsolve returned None")
        except Exception as sym_err:
            return VerificationSource(name=name, status="skip",
                                       message=f"WolframAlpha check skipped — could not obtain "
                                               f"reference solution from SymPy: {sym_err}",
                                       details={})

        # ── Step 2: build Wolfram-readable expression string ──────────────────
        # sp.mathematica_code converts SymPy expr to Mathematica/Wolfram syntax
        try:
            wolfram_expr = sp.mathematica_code(ref_expr)
        except Exception:
            wolfram_expr = str(ref_expr)

        # ── Step 3: ask Wolfram to evaluate at 5 sample points ────────────────
        fractions   = [0.10, 0.25, 0.50, 0.75, 0.90]
        sample_t    = [t0 + f * (t_end - t0) for f in fractions]
        wolfram_y, wolfram_t, errors = [], [], []

        for t_val in sample_t:
            # Build query: evaluate the expression numerically at a specific t
            # Use \b word-boundary so we don't replace 't' inside longer tokens
            expr_at_t = re.sub(r'\bt\b', f"({t_val:.6f})", wolfram_expr)
            query     = f"N[{expr_at_t}]"
            try:
                resp = requests.get(
                    "https://api.wolframalpha.com/v1/result",
                    params={"appid": wolfram_app_id, "i": query},
                    timeout=10,
                )
                text = resp.text.strip()
                # Short Answers returns a plain number for numeric queries
                nums = re.findall(r"-?\d+\.?\d*(?:[eE][+-]?\d+)?", text)
                if not nums:
                    continue
                w_val = float(nums[0])
                if not math.isfinite(w_val):
                    continue
                u_val = float(np.interp(t_val, t_arr, x_num))
                wolfram_y.append(w_val)
                wolfram_t.append(t_val)
                errors.append(abs(u_val - w_val))
            except Exception:
                continue

        if not errors:
            return VerificationSource(name=name, status="error",
                                       message="WolframAlpha returned no numeric responses. "
                                               "Check your App ID or network connection.",
                                       details={"sample_query": f"N[{wolfram_expr[:80]}]"})

        # ── Step 4: score ──────────────────────────────────────────────────────
        max_err  = float(max(errors))
        mean_err = float(sum(errors) / len(errors))
        scale    = max(max(abs(v) for v in wolfram_y), 1e-10)
        status   = "pass" if mean_err < 0.05 * scale else "fail"
        conf     = max(0.0, (1.0 - mean_err / scale) * 100.0) if status == "pass" \
                   else max(0.0, 100.0 * float(np.exp(-mean_err / (0.05 * scale))))

        msg = (f"Checked at {len(errors)}/5 sample points against SymPy reference. "
               f"Mean deviation = {mean_err:.3e}, max = {max_err:.3e}.")

        comparison_table = [
            {"t": wt, "WolframAlpha": wy,
             "Solver": float(np.interp(wt, t_arr, x_num)),
             "Error": e}
            for wt, wy, e in zip(wolfram_t, wolfram_y, errors)
        ]

        return VerificationSource(
            name=name, status=status, message=msg,
            max_error=max_err, mean_error=mean_err, confidence=conf,
            reference_t=wolfram_t, reference_y=wolfram_y,
            details={"comparison_table": comparison_table,
                     "points_checked": len(errors),
                     "reference_expression": str(ref_expr)[:200]},
        )

    except Exception as exc:
        return VerificationSource(name=name, status="error",
                                   message=f"Exception: {exc}", details={})


# ─────────────────────────────────────────────────────────────────────────────
# Check 3 — Energy Conservation
# ─────────────────────────────────────────────────────────────────────────────

def _check_energy(components, result: Dict) -> VerificationSource:
    name = "Energy Conservation"

    try:
        y_arr = np.array(result["y"])
        t_arr = np.array(result["t"])

        if components.order != 2 or y_arr.shape[0] < 2:
            return VerificationSource(name=name, status="skip",
                                       message="Requires 2nd-order ODE with velocity data (y.shape[0] >= 2).",
                                       details={})

        # Energy conservation only meaningful for unforced (homogeneous) systems.
        # Forced systems have external energy input so conservation does not apply.
        if not components.is_homogeneous:
            return VerificationSource(name=name, status="skip",
                                       message="Forced (non-homogeneous) ODE — energy is not conserved by design; check skipped.",
                                       details={})

        coeffs = _get_coeffs(components)
        if coeffs is None:
            return VerificationSource(name=name, status="skip",
                                       message="Could not extract coefficients for energy calculation.",
                                       details={})

        x = y_arr[0]
        v = y_arr[1]
        c = coeffs["c"]
        b = coeffs["b"]

        # E(t) = 0.5*v² + 0.5*c*x²  (kinetic + potential)
        E = 0.5 * v ** 2 + 0.5 * c * x ** 2
        E0 = float(E[0])

        if abs(E0) < 1e-12:
            return VerificationSource(name=name, status="skip",
                                       message="Initial energy is ~0; cannot normalise.",
                                       details={})

        delta_E = np.abs(E - E0)
        max_err  = float(np.max(delta_E))
        mean_err = float(np.mean(delta_E))

        if abs(b) < 1e-9:
            # Undamped conservative system: energy must stay constant (< 2% drift)
            max_rel = float(np.max(delta_E) / abs(E0))
            status = "pass" if max_rel < 0.02 else "fail"
            if status == "pass":
                conf = max(0.0, (1.0 - max_rel / 0.02) * 100.0)
            else:
                conf = max(0.0, 100.0 * float(np.exp(-max_rel / 0.02)))
            msg = f"Undamped homogeneous — max dE/E0 = {max_rel:.3e}. {'PASS (<2%)' if status == 'pass' else 'FAIL (>=2%)'}"
        else:
            # Damped homogeneous system: energy must be monotonically non-increasing.
            # Allow small numerical noise (< 0.1% of E0 per step).
            noise_tol = max(abs(E0) * 0.001, 1e-8)
            increases = np.diff(E)
            bad_increases = int(np.sum(increases > noise_tol))
            total_steps = len(increases)
            bad_frac = bad_increases / max(total_steps, 1)
            status = "pass" if bad_frac < 0.02 else "fail"
            conf = max(0.0, (1.0 - bad_frac / 0.02) * 100.0)
            msg = (f"Damped homogeneous — {bad_increases}/{total_steps} steps had unexpected energy increase "
                   f"({bad_frac * 100:.1f}%). Threshold 2%.")

        return VerificationSource(
            name=name,
            status=status,
            message=msg,
            max_error=max_err,
            mean_error=mean_err,
            confidence=conf,
            reference_t=t_arr.tolist(),
            reference_y=E.tolist(),
            details={"E0": E0, "damped": abs(b) > 1e-9},
        )

    except Exception as exc:
        return VerificationSource(name=name, status="error",
                                   message=f"Exception: {exc}", details={})


# ─────────────────────────────────────────────────────────────────────────────
# Check 4 — Cross-Method Agreement (RK45 reference)
# ─────────────────────────────────────────────────────────────────────────────

def _check_cross_method(components, result: Dict, ic: Dict, time_span) -> VerificationSource:
    name = "Cross-Method Agreement (RK45)"

    try:
        t_arr = np.array(result["t"])
        y_arr = np.array(result["y"])
        x_num = y_arr[0]

        x0 = float(ic.get("x", 1.0))
        dx0 = float(ic.get("dx", 0.0))
        t0 = float(time_span[0])
        t_end = float(time_span[1])

        # Pre-compile forcing function once, outside the ODE loop
        _forcing_fn = None
        if not components.is_homogeneous and components.forcing_function:
            try:
                import sympy as sp
                _t_sym   = sp.Symbol("t")
                _f_expr  = sp.sympify(str(components.forcing_function),
                                      locals={"t": _t_sym, "sin": sp.sin,
                                              "cos": sp.cos, "exp": sp.exp,
                                              "sqrt": sp.sqrt})
                _forcing_fn = sp.lambdify(_t_sym, _f_expr, modules="numpy")
            except Exception:
                _forcing_fn = None

        # Build ODE function from components
        def ode_fn(t, y):
            try:
                return components.ode_function(t, y)
            except AttributeError:
                pass
            # Fallback: reconstruct from coefficients
            coeffs = _get_coeffs(components)
            if coeffs:
                a, b, c = coeffs["a"], coeffs["b"], coeffs["c"]
                forcing = 0.0
                if _forcing_fn is not None:
                    try:
                        forcing = float(np.real(_forcing_fn(t)))
                    except Exception:
                        forcing = 0.0
                # x'' = (forcing - b*x' - c*x) / a
                return [y[1], (forcing - b * y[1] - c * y[0]) / a]
            raise ValueError("Cannot build ODE function")

        ref_sol = solve_ivp(
            ode_fn,
            [t0, t_end],
            [x0, dx0],
            method="RK45",
            rtol=1e-8,
            atol=1e-10,
            dense_output=True,
        )

        if not ref_sol.success:
            return VerificationSource(name=name, status="error",
                                       message=f"RK45 reference failed: {ref_sol.message}",
                                       details={})

        # Interpolate reference onto user's grid
        x_ref = ref_sol.sol(t_arr)[0]

        diff = np.abs(x_num - x_ref)
        max_err = float(np.max(diff))
        mean_err = float(np.mean(diff))
        scale = max(float(np.max(np.abs(x_ref))), 1e-10)
        norm_mean = mean_err / scale
        conf = max(0.0, (1.0 - norm_mean / 0.05) * 100.0)

        status = "pass" if norm_mean < 0.05 else "fail"
        msg = (f"Normalised mean error vs RK45 reference = {norm_mean:.3e}. "
               f"Threshold 5%. Confidence {conf:.1f}%.")

        return VerificationSource(
            name=name,
            status=status,
            message=msg,
            max_error=max_err,
            mean_error=mean_err,
            confidence=conf,
            reference_t=t_arr.tolist(),
            reference_y=x_ref.tolist(),
            details={"norm_mean_error": norm_mean, "rk45_status": ref_sol.message},
        )

    except Exception as exc:
        return VerificationSource(name=name, status="error",
                                   message=f"Exception: {exc}", details={})


# ─────────────────────────────────────────────────────────────────────────────
# Check 5 — ODE Residual Check
# ─────────────────────────────────────────────────────────────────────────────

def _check_residual(components, result: Dict) -> VerificationSource:
    name = "ODE Residual Check"

    try:
        if components.order != 2 or not components.is_linear:
            return VerificationSource(name=name, status="skip",
                                       message="Residual check only for 2nd-order linear ODEs.",
                                       details={})

        coeffs = _get_coeffs(components)
        if coeffs is None:
            return VerificationSource(name=name, status="skip",
                                       message="Cannot extract coefficients.",
                                       details={})

        a, b, c = coeffs["a"], coeffs["b"], coeffs["c"]
        t_arr = np.array(result["t"])
        y_arr = np.array(result["y"])
        x = y_arr[0]

        # Numerical differentiation
        xp = np.gradient(x, t_arr)
        xpp = np.gradient(xp, t_arr)

        # Compute forcing at each t
        f_arr = np.zeros_like(t_arr)
        if not components.is_homogeneous and components.forcing_function:
            try:
                import sympy as sp
                t_sym  = sp.Symbol("t")
                f_expr = sp.sympify(str(components.forcing_function),
                                    locals={"t": t_sym, "sin": sp.sin,
                                            "cos": sp.cos, "exp": sp.exp,
                                            "sqrt": sp.sqrt})
                f_lam  = sp.lambdify(t_sym, f_expr, modules=["numpy"])
                f_arr  = np.array([float(np.real(f_lam(ti))) for ti in t_arr])
            except Exception:
                pass

        residual = np.abs(a * xpp + b * xp + c * x - f_arr)

        # Exclude first/last 2 points (boundary artifacts from gradient)
        interior = residual[2:-2]
        x_interior = x[2:-2]

        if len(interior) == 0:
            return VerificationSource(name=name, status="skip",
                                       message="Not enough time points for residual check.",
                                       details={})

        mean_res = float(np.mean(interior))
        max_res = float(np.max(interior))
        scale = max(float(np.max(np.abs(x_interior))), 1e-10)
        norm_mean = mean_res / scale
        status = "pass" if norm_mean < 0.05 else "fail"
        if status == "pass":
            conf = max(0.0, (1.0 - norm_mean / 0.05) * 100.0)
        else:
            conf = max(0.0, 100.0 * float(np.exp(-norm_mean / 0.05)))
        msg = (f"Mean residual / max|x| = {norm_mean:.3e}. "
               f"Threshold 5%. Confidence {conf:.1f}%.")

        return VerificationSource(
            name=name,
            status=status,
            message=msg,
            max_error=max_res,
            mean_error=mean_res,
            confidence=conf,
            reference_t=None,
            reference_y=None,
            details={"norm_mean_residual": norm_mean,
                     "formula": f"{a}·x'' + {b}·x' + {c}·x - f(t) ≈ 0"},
        )

    except Exception as exc:
        return VerificationSource(name=name, status="error",
                                   message=f"Exception: {exc}", details={})


# ─────────────────────────────────────────────────────────────────────────────
# Check 6 — Initial Condition Satisfaction
# ─────────────────────────────────────────────────────────────────────────────

def _check_initial_conditions(result: Dict, ic: Dict) -> VerificationSource:
    name = "Initial Condition Satisfaction"

    try:
        x0 = float(ic.get("x", 1.0))
        dx0 = float(ic.get("dx", 0.0))

        y_arr = np.array(result["y"])
        x_got = float(y_arr[0][0])

        x_ok = abs(x_got - x0) < 1e-4
        v_ok = False
        v_err = None
        v_got = None

        if y_arr.shape[0] >= 2:
            v_got = float(y_arr[1][0])
            v_err = abs(v_got - dx0)
            v_ok = v_err < 1e-4

        x_err = abs(x_got - x0)
        all_ok = x_ok and (v_ok if v_got is not None else True)

        status = "pass" if all_ok else "fail"
        lines = [f"|x(0) - {x0}| = {x_err:.2e} → {'✓ PASS' if x_ok else '✗ FAIL'}"]
        if v_got is not None:
            lines.append(f"|v(0) - {dx0}| = {v_err:.2e} → {'✓ PASS' if v_ok else '✗ FAIL'}")
        msg = "  ".join(lines)

        conf = 100.0 if all_ok else (50.0 if x_ok or v_ok else 0.0)

        return VerificationSource(
            name=name,
            status=status,
            message=msg,
            max_error=float(max(x_err, v_err if v_err is not None else x_err)),
            mean_error=float((x_err + (v_err or x_err)) / 2),
            confidence=conf,
            reference_t=None,
            reference_y=None,
            details={
                "x0_expected": x0, "x0_got": x_got, "x0_pass": bool(x_ok),
                "dx0_expected": dx0, "dx0_got": v_got, "v0_pass": bool(v_ok),
            },
        )

    except Exception as exc:
        return VerificationSource(name=name, status="error",
                                   message=f"Exception: {exc}", details={})


# ─────────────────────────────────────────────────────────────────────────────
# Overall status aggregation
# ─────────────────────────────────────────────────────────────────────────────

def _aggregate(sources: List[VerificationSource]) -> tuple[str, float, str]:
    """Returns (overall_status, overall_confidence, summary)."""
    active = [s for s in sources if s.status in ("pass", "fail")]
    passed = [s for s in active if s.status == "pass"]
    failed = [s for s in active if s.status == "fail"]

    if not active:
        status = "partial"
    elif not failed:
        status = "verified"
    elif len(failed) >= len(passed):
        status = "failed"
    else:
        status = "warning"

    conf_sources = [s for s in sources if s.confidence is not None]
    overall_conf = float(np.mean([s.confidence for s in conf_sources])) if conf_sources else 0.0

    n_pass = len(passed)
    n_fail = len(failed)
    n_skip = sum(1 for s in sources if s.status in ("skip", "error"))
    summary = (f"{n_pass} passed, {n_fail} failed, {n_skip} skipped/error out of "
               f"{len(sources)} checks. Overall confidence: {overall_conf:.1f}%.")

    return status, overall_conf, summary


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

class ODEVerifier:
    """
    Runs 6 independent checks on a computed ODE solution.

    Usage
    -----
    verifier = ODEVerifier()
    report = verifier.verify(components, result, ic, time_span, wolfram_app_id=None)
    """

    def verify(
        self,
        components,          # ODEComponents from core/parser.py
        result: Dict,        # {"t": list, "y": list[list], "method": str, "stats": dict}
        ic: Dict,            # {"x": float, "dx": float}
        time_span,           # (t0, t_end)
        wolfram_app_id: Optional[str] = None,
    ) -> VerificationReport:
        t_start = time.perf_counter()

        sources: List[VerificationSource] = []

        # 1. Analytical library
        sources.append(_check_analytical(components, result, ic))

        # 2. WolframAlpha
        sources.append(_check_wolfram(components, result, ic, time_span, wolfram_app_id))

        # 3. Energy conservation
        sources.append(_check_energy(components, result))

        # 4. Cross-method (RK45 reference)
        sources.append(_check_cross_method(components, result, ic, time_span))

        # 5. ODE residual
        sources.append(_check_residual(components, result))

        # 6. Initial conditions
        sources.append(_check_initial_conditions(result, ic))

        overall_status, overall_conf, summary = _aggregate(sources)
        compute_ms = (time.perf_counter() - t_start) * 1000.0

        return VerificationReport(
            sources=sources,
            overall_status=overall_status,
            overall_confidence=overall_conf,
            summary=summary,
            compute_ms=compute_ms,
        )
