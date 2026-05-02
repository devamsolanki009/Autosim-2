"""
utils/solver_engine.py
──────────────────────
AutoSim ODE Solver Engine — 5-Step Pipeline

Step 1 — Parse & Restate
Step 2 — Generate solver() with CoT comments
Step 3 — Self-debug
Step 4 — Append eval + plot block
Step 5 — Refinement (called externally on error feedback)
"""

from __future__ import annotations
import re
import textwrap
from dataclasses import dataclass
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ParsedODE:
    """Result of Step 1 – structured representation of the user's ODE."""
    raw_equation: str
    order: int
    is_linear: bool
    is_homogeneous: bool
    is_stiff: bool
    has_partial_derivatives: bool
    variables: List[str]
    parameters: Dict[str, float]
    initial_conditions: Dict[str, float]
    time_span: tuple
    n_vars: int
    forcing_function: Optional[str]
    nonlinear_terms: List[str]
    natural_language: str


@dataclass
class SolverEngineResult:
    """Full output of the 5-step pipeline."""
    parsed: ParsedODE
    solver_code: str
    eval_code: str
    full_code: str
    debug_notes: List[str]
    method_chosen: str
    issues_found: List[str]
    is_valid: bool


# ─────────────────────────────────────────────────────────────────────────────
# Step 1 — Parse & Restate
# ─────────────────────────────────────────────────────────────────────────────

def _detect_partial_derivatives(eq: str) -> bool:
    pde_patterns = ['partial', 'd2u/dx', 'd2v/dx', 'nabla']
    eq_lower = eq.lower()
    for p in pde_patterns:
        if p in eq_lower:
            return True
    if '\u2202' in eq or '\u2207' in eq:
        return True
    return False


def _detect_order(eq: str) -> int:
    eq_clean = eq.replace(' ', '')
    primes = re.findall(r"x('*)", eq_clean)
    max_primes = max((len(p) for p in primes), default=0)
    if 'd2x' in eq_clean or "x''" in eq_clean:
        max_primes = max(max_primes, 2)
    if 'd3x' in eq_clean or "x'''" in eq_clean:
        max_primes = max(max_primes, 3)
    return max(max_primes, 1)


def _detect_nonlinear(eq: str) -> List[str]:
    patterns = [r'x\*\*\d+', r'x\*x', r'sin\(x\)', r'cos\(x\)', r'exp\(x\)', r'log\(x\)']
    found = []
    for p in patterns:
        found.extend(re.findall(p, eq))
    return found


def _extract_coefficients(eq: str) -> Dict[str, float]:
    coeffs: Dict[str, float] = {}
    patterns = [
        (r"([+-]?\d*\.?\d+)\*?x''", 'x2'),
        (r"([+-]?\d*\.?\d+)\*?x'",  'x1'),
        (r"([+-]?\d*\.?\d+)\*?x(?!['*])", 'x0'),
    ]
    for pattern, name in patterns:
        m = re.search(pattern, eq)
        if m:
            try:
                coeffs[name] = float(m.group(1))
            except ValueError:
                pass
    if "x''" in eq and 'x2' not in coeffs:
        coeffs['x2'] = 1.0
    if "x'" in eq and 'x1' not in coeffs:
        coeffs['x1'] = 1.0
    if re.search(r"(?<!['\*\d])x(?!['\*\d])", eq) and 'x0' not in coeffs:
        coeffs['x0'] = 1.0
    return coeffs


def _check_stiff(eq: str, coefficients: Dict[str, float]) -> bool:
    for val in coefficients.values():
        if abs(val) > 100:
            return True
    if 'stiff' in eq.lower() or '1000' in eq or '500' in eq:
        return True
    return False


def _build_natural_language(eq: str, ic: Dict[str, float], time_span: tuple,
                             order: int, is_linear: bool, is_stiff: bool,
                             nonlinear: List[str], forcing: Optional[str]) -> str:
    tp = 'linear' if is_linear else 'nonlinear'
    parts = [
        f"Solve the {tp} {order}-order ODE:  {eq}",
        f"Initial conditions: x(0) = {ic.get('x', 1)},  x'(0) = {ic.get('dx', 0)}",
        f"Time domain: t in [{time_span[0]}, {time_span[1]}]",
    ]
    if nonlinear:
        parts.append(f"Nonlinear terms detected: {', '.join(nonlinear)}")
    if forcing:
        parts.append(f"Forcing function (RHS): {forcing}")
    if is_stiff:
        parts.append("WARNING: Stiffness detected - will use implicit Radau solver.")
    return '\n'.join(parts)


def step1_parse(equation: str, ic: Dict[str, float], time_span: tuple) -> ParsedODE:
    order       = _detect_order(equation)
    nonlinear   = _detect_nonlinear(equation)
    coefficients = _extract_coefficients(equation)
    is_linear   = len(nonlinear) == 0
    is_stiff    = _check_stiff(equation, coefficients)
    has_pde     = _detect_partial_derivatives(equation)

    if '=' in equation:
        lhs, rhs = equation.split('=', 1)
    else:
        lhs, rhs = equation, '0'

    rhs = rhs.strip()
    is_homogeneous = rhs in ('0', '')
    forcing = rhs if not is_homogeneous else None
    n_vars  = order

    nl = _build_natural_language(equation, ic, time_span, order,
                                 is_linear, is_stiff, nonlinear, forcing)

    return ParsedODE(
        raw_equation=equation,
        order=order,
        is_linear=is_linear,
        is_homogeneous=is_homogeneous,
        is_stiff=is_stiff,
        has_partial_derivatives=has_pde,
        variables=['x'],
        parameters={},
        initial_conditions=ic,
        time_span=time_span,
        n_vars=n_vars,
        forcing_function=forcing,
        nonlinear_terms=nonlinear,
        natural_language=nl,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Code Generation
# ─────────────────────────────────────────────────────────────────────────────

def _py_forcing(forcing_str: str) -> str:
    return (forcing_str
            .replace('cos(t)', 'np.cos(t)')
            .replace('sin(t)', 'np.sin(t)')
            .replace('exp(t)', 'np.exp(t)')
            .replace('tan(t)', 'np.tan(t)')
            .replace('^', '**'))


def _build_ode_system_body(parsed: ParsedODE) -> str:
    eq      = parsed.raw_equation
    order   = parsed.order
    forcing = parsed.forcing_function or '0'
    pf      = _py_forcing(forcing)

    if order == 1:
        rhs = pf if pf != '0' else '-y[0]'
        return (
            "    # 1st-order system: dy/dt = f(y, t)\n"
            "    dydt = " + rhs + "\n"
            "    return [dydt]"
        )

    # 2nd-order
    coeffs   = _extract_coefficients(eq)
    cx1      = coeffs.get('x1', 0.0)
    cx0      = coeffs.get('x0', 0.0)

    nl_lines = []
    for term in parsed.nonlinear_terms:
        py_term = term.replace('x', 'y[0]').replace('^', '**')
        nl_lines.append("    nl_term += " + py_term + "  # nonlinear: " + term)
    nl_block = '\n'.join(nl_lines) if nl_lines else "    pass  # no nonlinear terms"

    lines = [
        "    # 2nd-order ODE reduced to 1st-order system:",
        "    # State: y = [x, x']  =>  derivatives = [x', x'']",
        "    #",
        "    # CoT:",
        "    #   x'' = f(t) - " + str(cx1) + "*x' - " + str(cx0) + "*x - NL(x)",
        "    #   where f(t) = " + pf,
        "    x_pos = y[0]   # x",
        "    x_vel = y[1]   # x'",
        "    f_t = " + pf,
        "    nl_term = 0.0",
        nl_block,
        "    x_acc = f_t - " + str(cx1) + " * x_vel - " + str(cx0) + " * x_pos - nl_term",
        "    return [x_vel, x_acc]",
    ]
    return '\n'.join(lines)


def step2_generate_code(parsed: ParsedODE) -> str:
    method  = 'Radau' if parsed.is_stiff else 'RK45'
    n_vars  = parsed.n_vars
    t0, tf  = parsed.time_span

    ic_list: List[float] = [parsed.initial_conditions.get('x', 1.0)]
    if n_vars >= 2:
        ic_list.append(parsed.initial_conditions.get('dx', 0.0))
    ic_repr = repr(ic_list)

    nl_comment = parsed.natural_language.replace('\n', '\n# ')
    param_list = ', '.join('y' + str(i + 1) + '_0' for i in range(n_vars))
    method_comment = (
        '# -> Radau (L-stable implicit, handles stiff ODEs robustly)'
        if parsed.is_stiff else
        '# -> RK45 (explicit Runge-Kutta, efficient for non-stiff problems)'
    )
    stiff_flag = str(parsed.is_stiff)

    ode_body = _build_ode_system_body(parsed)

    code = (
        "# =========================================================\n"
        "# AutoSim ODE Solver Engine -- Generated Code\n"
        "# Pipeline: Parse -> Generate -> Self-debug -> Evaluate\n"
        "# =========================================================\n"
        "\n"
        "# STEP 1 -- Problem Statement\n"
        "# " + nl_comment + "\n"
        "\n"
        "import numpy as np\n"
        "from scipy.integrate import solve_ivp\n"
        "\n"
        "\n"
        "def ode_system(t, y, params=None):\n"
        '    """\n'
        "    ODE right-hand side in first-order system form.\n"
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    t      : float          -- current time\n"
        "    y      : array-like     -- state vector [x, x', ...]\n"
        "    params : dict, optional -- named parameters\n"
        "\n"
        "    Returns\n"
        "    -------\n"
        "    dydt : list -- derivatives of state vector\n"
        '    """\n'
        + ode_body + "\n"
        "\n"
        "\n"
        "def solver(y0, t_span, t_eval, params=None):\n"
        '    """\n'
        "    Solves the ODE system for all times in t_eval.\n"
        "\n"
        "    Parameters\n"
        "    ----------\n"
        "    y0     : list or np.ndarray  -- initial conditions [" + param_list + "]\n"
        "    t_span : tuple               -- (t_start, t_end)\n"
        "    t_eval : np.ndarray          -- time points to evaluate solution at\n"
        "    params : dict, optional      -- named parameters for the ODE\n"
        "\n"
        "    Returns\n"
        "    -------\n"
        "    t : np.ndarray -- time array, shape (len(t_eval),)\n"
        "    y : np.ndarray -- solution array, shape (" + str(n_vars) + ", len(t_eval))\n"
        '    """\n'
        "    # CoT: Method selection\n"
        "    # Stiffness detected: " + stiff_flag + "\n"
        "    " + method_comment + "\n"
        "    method = '" + method + "'\n"
        "\n"
        "    # Ensure y0 is a proper list\n"
        "    y0 = list(np.atleast_1d(y0))\n"
        "\n"
        "    sol = solve_ivp(\n"
        "        fun=lambda t, y: ode_system(t, y, params),\n"
        "        t_span=t_span,\n"
        "        y0=y0,\n"
        "        method=method,\n"
        "        t_eval=t_eval,\n"
        "        dense_output=False,\n"
        "        rtol=1e-8,\n"
        "        atol=1e-10,\n"
        "    )\n"
        "\n"
        "    if not sol.success:\n"
        "        raise RuntimeError(f'ODE integration failed: {sol.message}')\n"
        "\n"
        "    # sol.y shape: (n_vars, len(t_eval))\n"
        "    return sol.t, sol.y\n"
        "\n"
        "\n"
        "# ── Default parameters (edit as needed) ─────────────────────────────\n"
        "y0     = " + ic_repr + "\n"
        "t_span = (" + str(t0) + ", " + str(tf) + ")\n"
        "t_eval = np.linspace(" + str(t0) + ", " + str(tf) + ", 1000)\n"
        "params = None\n"
    )
    return code


# ─────────────────────────────────────────────────────────────────────────────
# Step 3 — Self-Debug
# ─────────────────────────────────────────────────────────────────────────────

def step3_self_debug(code: str, parsed: ParsedODE):
    issues: List[str] = []
    notes:  List[str] = []

    if 'import numpy' not in code:
        issues.append("Missing 'import numpy as np'")
        code = "import numpy as np\n" + code
    if 'from scipy.integrate import solve_ivp' not in code:
        issues.append("Missing scipy solve_ivp import")
        code = "from scipy.integrate import solve_ivp\n" + code

    if 'def ode_system(' not in code:
        issues.append("ode_system() function missing")
    else:
        notes.append("OK: ode_system() defined")

    if 'def solver(y0, t_span, t_eval' not in code:
        issues.append("solver() function signature incorrect")
    else:
        notes.append("OK: solver() signature correct")

    if 'return sol.t, sol.y' not in code:
        issues.append("solver() does not return (t, y) tuple")
    else:
        notes.append("OK: Returns (t, y) -- shapes: (n_pts,) and (n_vars, n_pts)")

    ic_list: List[float] = [parsed.initial_conditions.get('x', 1.0)]
    if parsed.n_vars >= 2:
        ic_list.append(parsed.initial_conditions.get('dx', 0.0))
    if len(ic_list) != parsed.n_vars:
        issues.append(
            "y0 length mismatch: got " + str(len(ic_list)) +
            ", expected " + str(parsed.n_vars)
        )
    else:
        notes.append(
            "OK: y0 length = " + str(len(ic_list)) +
            " = n_vars (" + str(parsed.n_vars) + ")"
        )

    if parsed.has_partial_derivatives:
        issues.append("PDE detected -- AutoSim Phase-1 only handles ODEs.")

    if not issues:
        notes.append("Self-debug PASSED -- code is ready to run")

    return code, issues, notes


# ─────────────────────────────────────────────────────────────────────────────
# Step 4 — Evaluation Block
# ─────────────────────────────────────────────────────────────────────────────

def step4_eval_block(parsed: ParsedODE) -> str:
    n_vars = parsed.n_vars
    subplot_n = '2' if n_vars >= 2 else '1'
    ax0_ref   = 'axes[0]' if n_vars >= 2 else 'axes'

    phase_lines = ""
    if n_vars >= 2:
        phase_lines = (
            "\n"
            "ax1 = axes[1]\n"
            "ax1.plot(y[0], y[1], color='#a78bfa', lw=1.6, alpha=0.85)\n"
            "ax1.set_xlabel('x', fontsize=11, color='#94a3b8')\n"
            "ax1.set_ylabel(\"x'\", fontsize=11, color='#94a3b8')\n"
            "ax1.set_title('Phase Portrait', fontsize=12, fontweight='bold', color='#f1f5f9')\n"
            "ax1.grid(True, alpha=0.15, color='#334155')\n"
            "ax1.set_facecolor('#030712')\n"
            "ax1.tick_params(colors='#64748b')\n"
        )

    return (
        "\n"
        "# --- EVALUATION ---\n"
        "import matplotlib.pyplot as plt\n"
        "\n"
        "t, y = solver(y0, t_span, t_eval, params)\n"
        "\n"
        "# Plot results\n"
        "labels = ['x(t)', \"x'(t)\", \"x''(t)\"][:len(y)]\n"
        "colors = ['#22d3ee', '#a78bfa', '#34d399']\n"
        "\n"
        "fig, axes = plt.subplots(1, " + subplot_n + ", figsize=(13, 4.5))\n"
        "fig.patch.set_facecolor('#0d1117')\n"
        "\n"
        "ax0 = " + ax0_ref + "\n"
        "for i, (yi, lbl, col) in enumerate(zip(y, labels, colors)):\n"
        "    if i == 0:\n"
        "        ax0.plot(t, yi, color=col, lw=2, label=lbl)\n"
        "ax0.set_xlabel('Time (t)', fontsize=11, color='#94a3b8')\n"
        "ax0.set_ylabel('x(t)', fontsize=11, color='#94a3b8')\n"
        "ax0.set_title('AutoSim -- ODE Solution', fontsize=12, fontweight='bold', color='#f1f5f9')\n"
        "ax0.legend(fontsize=9)\n"
        "ax0.grid(True, alpha=0.15, color='#334155')\n"
        "ax0.set_facecolor('#030712')\n"
        "ax0.tick_params(colors='#64748b')\n"
        + phase_lines +
        "\n"
        "plt.tight_layout()\n"
        "plt.show()\n"
        "\n"
        "# Key statistics\n"
        "x = y[0]\n"
        "print('x_final =', round(float(x[-1]), 6))\n"
        "print('x_max   =', round(float(x.max()), 6))\n"
        "print('x_min   =', round(float(x.min()), 6))\n"
        "print('x_std   =', round(float(x.std()), 6))\n"
        "\n"
        "# Convergence check (optional)\n"
        "t_coarse = np.linspace(t_span[0], t_span[1], 200)\n"
        "t_fine   = np.linspace(t_span[0], t_span[1], 2000)\n"
        "_, y_coarse = solver(y0, t_span, t_coarse, params)\n"
        "_, y_fine   = solver(y0, t_span, t_fine,   params)\n"
        "x_ci = np.interp(t_fine, t_coarse, y_coarse[0])\n"
        "nrmse = (np.mean((y_fine[0] - x_ci)**2)**0.5) / (y_fine[0].max() - y_fine[0].min() + 1e-12)\n"
        "print('nRMSE (coarse vs fine):', round(float(nrmse), 8), '  (< 1e-3 is excellent)')\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Step 5 — Refinement
# ─────────────────────────────────────────────────────────────────────────────

def step5_refine(original_result: SolverEngineResult,
                 error_type: str,
                 error_detail: str) -> str:
    code   = original_result.solver_code
    advice: List[str] = []

    if error_type in ('oscillation', 'instability'):
        code = code.replace("method = 'RK45'", "method = 'Radau'")
        code = code.replace("method = 'DOP853'", "method = 'Radau'")
        advice.append(
            "WHY: Oscillations/instability => ODE is stiff. "
            "Switched RK45 -> Radau (L-stable implicit, cannot go unstable for stiff problems)."
        )
    elif error_type == 'high_error':
        code = code.replace('rtol=1e-8', 'rtol=1e-10')
        code = code.replace('atol=1e-10', 'atol=1e-12')
        advice.append(
            "WHY: High error detected. Tightened tolerances rtol=1e-10, atol=1e-12 "
            "=> smaller steps, better accuracy at slight runtime cost."
        )
    elif error_type == 'slow':
        code = code.replace("method = 'Radau'", "method = 'LSODA'")
        code = code.replace("method = 'RK45'",  "method = 'LSODA'")
        code = code.replace(
            'np.linspace(t_span[0], t_span[1], 1000)',
            'np.linspace(t_span[0], t_span[1], 400)'
        )
        advice.append(
            "WHY: Slow runtime. Switched to LSODA (auto stiff/non-stiff) "
            "and reduced t_eval to 400 points."
        )
    elif error_type == 'runtime':
        advice.append(
            "WHY: Runtime error '" + error_detail + "'. "
            "Ensure your equation uses x, x', x'' notation, "
            "all parameters are numeric, and ICs are floats."
        )

    header = '\n'.join("# REFINEMENT NOTE: " + a for a in advice)
    return header + "\n\n" + code


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(equation: str,
                 ic: Dict[str, float],
                 time_span: tuple) -> SolverEngineResult:
    parsed = step1_parse(equation, ic, time_span)

    if parsed.has_partial_derivatives:
        return SolverEngineResult(
            parsed=parsed,
            solver_code='',
            eval_code='',
            full_code=(
                "# PDE DETECTED\n"
                "# AutoSim Phase-1 only supports ODEs.\n"
                "# PDE support coming in a future phase.\n"
                "# Please rephrase as an ODE."
            ),
            debug_notes=['PDE detected -- cannot generate solver'],
            method_chosen='N/A',
            issues_found=['Partial differential equation -- not supported in Phase-1'],
            is_valid=False,
        )

    solver_code               = step2_generate_code(parsed)
    solver_code, issues, notes = step3_self_debug(solver_code, parsed)
    eval_code                  = step4_eval_block(parsed)
    full_code                  = solver_code + eval_code

    return SolverEngineResult(
        parsed=parsed,
        solver_code=solver_code,
        eval_code=eval_code,
        full_code=full_code,
        debug_notes=notes,
        method_chosen='Radau' if parsed.is_stiff else 'RK45',
        issues_found=issues,
        is_valid=len(issues) == 0,
    )
