"""
ODE Solver System — Streamlit UI  (Multi-Method Dropdown Edition)
─────────────────────────────────────────────────────────────────
Drop-in replacement for the original app.py.
Adds a single dropdown to pick the solving method, plus a
"Compare All Methods" option that runs every method and shows
overlapping plots, a stats table, and compute-time bars.

File layout expected
────────────────────
ode_solver_complete/
├── core/parser.py
├── core/router.py
├── solvers/symbolic.py
├── solvers/numerical.py
├── solvers/euler.py          ← NEW (provided separately)
├── solvers/laplace.py        ← NEW (provided separately)
├── utils/visualization.py
├── llm_integration/enhanced_solver.py
├── main.py
└── app.py                    ← THIS FILE
"""

# ── stdlib / third-party ──────────────────────────────────────────────────────
import sys, time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import pandas as pd
import streamlit as st

# ── local imports ─────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from main import ODESolverSystem, CompleteSolution
from core.parser import ODEParser
from core.router import ODERouter
from solvers.symbolic  import SymbolicSolver,  SymbolicSolution
from solvers.numerical import NumericalSolver,  NumericalSolution
from solvers.euler     import EulerSolver,      EulerSolution
from solvers.laplace   import LaplaceSolver,    LaplaceSolution
from llm_integration.enhanced_solver import LLMEnhancedSolver


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG & CSS
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="ODE Solver",
    page_icon="∫",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* ── typography ── */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Sora:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Sora', sans-serif; }

/* ── header ── */
.ode-hero {
    padding: 1.6rem 0 0.4rem;
    text-align: center;
}
.ode-hero h1 {
    font-size: 2.4rem; font-weight: 800;
    background: linear-gradient(135deg, #0f172a 0%, #1e40af 50%, #7c3aed 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0; letter-spacing: -1px;
}
.ode-hero p {
    color: #64748b; font-size: 0.9rem; margin-top: 4px;
    font-family: 'JetBrains Mono', monospace; letter-spacing: 1px;
}

/* ── method badge ── */
.mbadge {
    display: inline-block; padding: 3px 12px; border-radius: 20px;
    font-size: 0.72rem; font-weight: 600; letter-spacing: 0.5px;
    font-family: 'JetBrains Mono', monospace; margin-left: 6px;
}
.mb-sym  { background:#ede9fe; color:#5b21b6; }
.mb-num  { background:#dcfce7; color:#166534; }
.mb-edu  { background:#fef3c7; color:#92400e; }
.mb-lap  { background:#dbeafe; color:#1e40af; }
.mb-cmp  { background:#f1f5f9; color:#334155; }

/* ── info / stat cards ── */
.stat-row { display:flex; gap:12px; margin:12px 0; }
.stat-card {
    flex:1; background:#f8fafc; border:1px solid #e2e8f0;
    border-radius:10px; padding:.9rem 1rem; text-align:center;
}
.stat-label { font-size:.68rem; color:#94a3b8; text-transform:uppercase;
              letter-spacing:1px; font-family:'JetBrains Mono',monospace; }
.stat-val   { font-size:1.35rem; font-weight:700; color:#0f172a;
              font-family:'JetBrains Mono',monospace; margin-top:3px; }

/* ── callout boxes ── */
.box { padding:.85rem 1.1rem; border-radius:8px; margin:8px 0; font-size:.88rem; }
.box-info  { background:#f0f9ff; border-left:3px solid #0284c7; }
.box-ok    { background:#f0fdf4; border-left:3px solid #16a34a; }
.box-warn  { background:#fffbeb; border-left:3px solid #d97706; }
.box-err   { background:#fef2f2; border-left:3px solid #dc2626; }

/* ── step box ── */
.step-box  { background:#fafafa; border:1px solid #e5e7eb;
             border-radius:8px; padding:.85rem 1.1rem; margin:6px 0; }

/* ── sidebar ── */
section[data-testid="stSidebar"] { background:#fafafa; border-right:1px solid #e2e8f0; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

# Dropdown options shown to the user → (internal key, badge class, category)
METHOD_OPTIONS: Dict[str, tuple] = {
    "Symbolic  — exact formula (SymPy)":          ("symbolic",  "mb-sym", "symbolic"),
    "Laplace Transform  — exact via s-domain":     ("laplace",   "mb-lap", "symbolic"),
    "RK45  — standard numerical (SciPy)":          ("rk45",      "mb-num", "numerical"),
    "Radau  — implicit / stiff systems (SciPy)":   ("radau",     "mb-num", "numerical"),
    "Forward Euler  — educational / simple":       ("euler_fwd", "mb-edu", "educational"),
    "Improved Euler (Heun's)  — educational":      ("euler_imp", "mb-edu", "educational"),
    "━━  Compare All Methods  ━━":                 ("compare",   "mb-cmp", "special"),
}

# Plotting colours per key
METHOD_COLOR = {
    "symbolic":  "#7c3aed",
    "laplace":   "#2563eb",
    "rk45":      "#16a34a",
    "radau":     "#ca8a04",
    "euler_fwd": "#dc2626",
    "euler_imp": "#db2777",
}

LINEAR_ONLY = {"symbolic", "laplace"}   # not valid for nonlinear ODEs

EXAMPLES = {
    "Simple Harmonic":  "x'' + x = 0",
    "Damped":           "x'' + 2*x' + x = 0",
    "Forced Duffing":   "x'' + 0.2*x' + x + 0.1*x**3 = cos(t)",
    "Van der Pol":      "x'' - (1 - x**2)*x' + x = 0",
    "Stiff":            "x'' + 1000*x' + x = 0",
    "Underdamped":      "x'' + 0.5*x' + 4*x = 0",
    "Overdamped":       "x'' + 5*x' + 4*x = 0",
    "Forced Harmonic":  "x'' + 0.1*x' + x = sin(2*t)",
}


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

def _init_state():
    defaults = {
        "equation":         "x'' + 0.2*x' + x = cos(t)",
        "result":           None,   # single-method result dict
        "compare_results":  None,   # list of result dicts (compare all)
        "parser":           ODEParser(),
        "sym_solver":       SymbolicSolver(),
        "num_solver":       NumericalSolver(),
        "euler_solver":     EulerSolver(),
        "lap_solver":       LaplaceSolver(),
        "basic_solver":     ODESolverSystem(),
        "llm_solver":       LLMEnhancedSolver(use_llm=True),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ══════════════════════════════════════════════════════════════════════════════
#  SOLVER DISPATCH
# ══════════════════════════════════════════════════════════════════════════════

def _run_one(key: str,
             components,
             ic: Dict,
             time_span: tuple,
             display_name: str) -> Dict:
    """
    Run a single method and return a unified result dict:
    {
      key, display_name, color,
      success, message,
      t, y,               ← numpy arrays (or None for pure-symbolic)
      solution_obj,       ← raw solver output
      stats,              ← {x_final, x_max, x_min, x_mean, ...}
      compute_ms,
      steps,              ← list of step objects (symbolic/laplace/euler)
    }
    """
    t0 = time.perf_counter()
    color = METHOD_COLOR.get(key, "#64748b")
    base = dict(key=key, display_name=display_name, color=color,
                t=None, y=None, solution_obj=None,
                stats={}, steps=[], success=False, message="")

    try:
        if key == "symbolic":
            sol = st.session_state.sym_solver.solve(components, ic)
            t_arr, y_arr = _sample_symbolic(sol, time_span)
            base.update(success=True, message="Exact symbolic solution.",
                        t=t_arr, y=y_arr, solution_obj=sol,
                        stats=_stats(t_arr, y_arr),
                        steps=sol.derivation_steps)

        elif key == "laplace":
            sol = st.session_state.lap_solver.solve(components, ic)
            t_arr, y_arr = None, None
            if sol.success and sol.x_of_t is not None:
                t_arr, y_arr = _sample_expr(sol.x_of_t, time_span)
            base.update(success=sol.success, message=sol.message,
                        t=t_arr, y=y_arr, solution_obj=sol,
                        stats=sol.statistics,
                        steps=sol.derivation_steps)

        elif key in ("rk45", "radau"):
            scipy_method = key.upper()
            sol = st.session_state.num_solver.solve(
                components, ic, time_span=time_span, method=scipy_method)
            base.update(success=sol.success, message=sol.message,
                        t=sol.t, y=sol.y, solution_obj=sol,
                        stats=sol.statistics)

        elif key == "euler_fwd":
            sol = st.session_state.euler_solver.solve(
                components, ic, time_span=time_span, variant="forward")
            base.update(success=sol.success, message=sol.message,
                        t=sol.t, y=sol.y, solution_obj=sol,
                        stats=sol.statistics, steps=sol.steps_table)

        elif key == "euler_imp":
            sol = st.session_state.euler_solver.solve(
                components, ic, time_span=time_span, variant="improved")
            base.update(success=sol.success, message=sol.message,
                        t=sol.t, y=sol.y, solution_obj=sol,
                        stats=sol.statistics, steps=sol.steps_table)

    except Exception as e:
        base.update(success=False, message=str(e))

    base["compute_ms"] = (time.perf_counter() - t0) * 1000
    return base


def _all_method_keys(components) -> List[str]:
    keys = ["symbolic", "laplace", "rk45", "radau", "euler_fwd", "euler_imp"]
    if not components.is_linear:
        keys = [k for k in keys if k not in LINEAR_ONLY]
    return keys


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _sample_symbolic(sol, time_span):
    import sympy as sp
    t_sym = sp.Symbol('t', positive=True)
    expr  = sol.particular_solution or sol.general_solution
    return _sample_expr(expr, time_span)


def _sample_expr(expr, time_span):
    import sympy as sp
    t_sym  = sp.Symbol('t', positive=True)
    t_arr  = np.linspace(time_span[0], time_span[1], 1000)
    try:
        f      = sp.lambdify(t_sym, expr, modules=['numpy'])
        x_vals = np.array([float(np.real(f(ti))) for ti in t_arr])
        return t_arr, x_vals.reshape(1, -1)
    except Exception:
        return t_arr, np.zeros((1, len(t_arr)))


def _stats(t, y) -> Dict:
    if y is None or y.size == 0:
        return {}
    x = y[0]
    return {
        "x_final": float(x[-1]),
        "x_max":   float(np.max(x)),
        "x_min":   float(np.min(x)),
        "x_mean":  float(np.mean(x)),
        "x_std":   float(np.std(x)),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown("## ∫ ODE Solver")
        st.divider()

        # ── Equation ──────────────────────────────────────────────────
        st.markdown("**1 · Equation**")
        equation = st.text_area(
            label="eq", label_visibility="collapsed",
            value=st.session_state.equation, height=80,
            help="Use x (dependent) and t (independent). "
                 "x'' = second derivative, x' = first derivative."
        )

        with st.expander("📚 Example equations"):
            cols = st.columns(2)
            for i, (name, val) in enumerate(EXAMPLES.items()):
                if cols[i % 2].button(name, key=f"ex_{name}", use_container_width=True):
                    st.session_state.equation = val
                    st.rerun()

        st.divider()

        # ── Initial conditions ─────────────────────────────────────────
        st.markdown("**2 · Initial Conditions**")
        c1, c2 = st.columns(2)
        x0  = c1.number_input("x(0)",  value=1.0, step=0.1, format="%.2f")
        dx0 = c2.number_input("x'(0)", value=0.0, step=0.1, format="%.2f")

        st.divider()

        # ── Time span ──────────────────────────────────────────────────
        st.markdown("**3 · Time Range**")
        c1, c2 = st.columns(2)
        t_start = c1.number_input("Start", value=0.0,  step=1.0,  format="%.1f")
        t_end   = c2.number_input("End",   value=50.0, step=5.0,  format="%.1f")

        st.divider()

        # ── Method dropdown ────────────────────────────────────────────
        st.markdown("**4 · Solving Method**")
        method_label = st.selectbox(
            label="method", label_visibility="collapsed",
            options=list(METHOD_OPTIONS.keys()),
            index=2,   # default: RK45
            help="Choose one method, or select 'Compare All' to run every method."
        )

        st.divider()

        # ── LLM insights toggle ────────────────────────────────────────
        use_llm = st.checkbox(
            "Enable LLM Insights",
            value=False,
            help="Adds an AI-generated plain-English interpretation tab."
        )

        st.divider()

        # ── Solve button ───────────────────────────────────────────────
        solve_btn = st.button("🚀 Solve ODE", type="primary",
                              use_container_width=True)

        # ── Zero-hallucination note ────────────────────────────────────
        st.markdown("""
        <div class="box box-info" style="font-size:.78rem;margin-top:1rem;">
            <strong>🔒 Zero Hallucination</strong><br>
            All maths: SymPy · SciPy · NumPy<br>
            LLM = interpretation only
        </div>""", unsafe_allow_html=True)

        return dict(
            equation=equation,
            ic={"x": x0, "dx": dx0},
            time_span=(t_start, t_end),
            method_label=method_label,
            use_llm=use_llm,
            solve=solve_btn,
        )


# ══════════════════════════════════════════════════════════════════════════════
#  RENDER HELPERS — single method
# ══════════════════════════════════════════════════════════════════════════════

def _stat_cards(stats: Dict):
    """Render 4 stat cards in a row."""
    keys   = ["x_final", "x_max", "x_min", "x_std"]
    labels = ["Final x", "Max x", "Min x", "Std dev"]
    cols   = st.columns(4)
    for col, lbl, k in zip(cols, labels, keys):
        val = stats.get(k)
        col.markdown(f"""
        <div class="stat-card">
          <div class="stat-label">{lbl}</div>
          <div class="stat-val">{f"{val:.5f}" if val is not None else "—"}</div>
        </div>""", unsafe_allow_html=True)


def _plot_single(result: Dict):
    """Time-series + phase portrait for one method."""
    if result["t"] is None or result["y"] is None:
        st.info("No time-series data for this method (pure symbolic).")
        return

    t, y   = result["t"], result["y"]
    color  = result["color"]
    name   = result["display_name"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.patch.set_facecolor("#fafafa")

    # x(t)
    axes[0].plot(t, y[0], color=color, lw=2)
    axes[0].set_xlabel("t", fontsize=11)
    axes[0].set_ylabel("x(t)", fontsize=11)
    axes[0].set_title(f"{name} — x(t) vs t", fontsize=12, fontweight="bold")
    axes[0].grid(True, alpha=0.25)
    axes[0].set_facecolor("#ffffff")

    # Phase portrait
    if y.shape[0] > 1:
        axes[1].plot(y[0], y[1], color=color, lw=1.6, alpha=0.85)
        axes[1].set_xlabel("x", fontsize=11)
        axes[1].set_ylabel("x′", fontsize=11)
        axes[1].set_title("Phase Portrait", fontsize=12, fontweight="bold")
    else:
        axes[1].axis("off")
    axes[1].grid(True, alpha=0.25)
    axes[1].set_facecolor("#ffffff")

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def _render_symbolic_steps(steps):
    """Derivation steps from symbolic or Laplace solver."""
    for step in steps:
        with st.container():
            st.markdown(f"**Step {step.step_number} — {step.description}**")
            try:
                st.latex(step.latex)
            except Exception:
                st.code(step.equation)
            st.divider()


def _render_euler_table(steps_table, sol_obj):
    """First-10-steps table for Euler methods."""
    if not steps_table:
        return
    df = pd.DataFrame(steps_table)
    st.dataframe(df, use_container_width=True, hide_index=True)
    if sol_obj is not None:
        st.markdown(
            f"<div class='box box-info'>Step size <b>h = {sol_obj.step_size:.6f}</b> · "
            f"Total steps: <b>{len(sol_obj.t)-1}</b></div>",
            unsafe_allow_html=True)


def render_single_method(result: Dict, classification: Dict,
                          routing_decision, use_llm: bool,
                          llm_result=None):
    """Full result view for a single method — split into 4 tabs."""
    key  = result["key"]
    name = result["display_name"]
    badge_cls = METHOD_OPTIONS.get(
        next((k for k in METHOD_OPTIONS if METHOD_OPTIONS[k][0] == key), ""),
        ("", "mb-num", ""))[1]

    # Header shown above all tabs
    st.markdown(
        f"### {name} "
        f"<span class='mbadge {badge_cls}'>{key.upper()}</span>",
        unsafe_allow_html=True)

    if not result["success"]:
        st.markdown(
            f"<div class='box box-err'>❌ {result['message']}</div>",
            unsafe_allow_html=True)
        return

    steps   = result.get("steps", [])
    sol_obj = result.get("solution_obj")

    # ── Four top-level tabs ────────────────────────────────────────────
    tab_results, tab_llm, tab_tech, tab_about = st.tabs([
        "📊 Results",
        "🤖 LLM Insights",
        "🔧 Technical Details",
        "📖 About",
    ])

    # ══════════════════════════════════════════════════════════════════
    # TAB 1 — Results
    # ══════════════════════════════════════════════════════════════════
    with tab_results:

        # 1. Classification
        st.markdown("#### 1️⃣ Equation Classification")
        cols = st.columns(4)
        items = [
            ("Order",  str(classification.get("order", "?")),                    "📐"),
            ("Type",   "Linear" if classification.get("linear") else "Nonlinear","🔢"),
            ("Family", classification.get("family", "—"),                        "🏷️"),
            ("Stiff",  "Yes ⚠️" if classification.get("stiff") else "No ✓",     "⚡"),
        ]
        for col, (lbl, val, ico) in zip(cols, items):
            col.metric(f"{ico} {lbl}", val)

        st.divider()

        # 2. Solver decision
        st.markdown("#### 2️⃣ Solver Decision")
        c1, c2, c3 = st.columns(3)
        c1.markdown(
            f"<div class='box box-info'><b>Method:</b> {key.upper()}<br>"
            f"<b>Compute time:</b> {result['compute_ms']:.1f} ms</div>",
            unsafe_allow_html=True)
        c2.markdown(
            f"<div class='box box-ok'><b>Reason:</b><br>{routing_decision.reason}</div>",
            unsafe_allow_html=True)
        stiff_icon = "🔴" if routing_decision.stiffness_detected else "🟢"
        c3.markdown(
            f"<div class='box box-info'><b>Stiffness:</b> {stiff_icon}<br>"
            f"<b>Family:</b> {routing_decision.equation_family}</div>",
            unsafe_allow_html=True)

        st.divider()

        # 3. Step-by-step derivation (symbolic / Laplace / Euler)
        if key in ("symbolic", "laplace") and steps:
            st.markdown("#### 3️⃣ Step-by-Step Derivation")
            with st.expander("View all derivation steps", expanded=False):
                _render_symbolic_steps(steps)
            st.divider()

        elif key in ("euler_fwd", "euler_imp") and isinstance(steps, list) \
                and steps and isinstance(steps[0], dict):
            st.markdown("#### 3️⃣ Integration Steps (first 10)")
            _render_euler_table(steps, sol_obj)
            st.divider()

        # 4. Statistics
        st.markdown("#### 4️⃣ Solution Statistics")
        _stat_cards(result["stats"])
        s = result["stats"]
        if sol_obj and hasattr(sol_obj, "statistics"):
            full = sol_obj.statistics
            if "period_estimate" in full:
                st.markdown(
                    f"**Estimated Period:** {full['period_estimate']:.4f} s  |  "
                    f"**Frequency:** {full['frequency_estimate']:.4f} Hz")

        st.divider()

        # 5. Visualization
        st.markdown("#### 5️⃣ Visualization")
        _plot_single(result)

    # ══════════════════════════════════════════════════════════════════
    # TAB 2 — LLM Insights
    # ══════════════════════════════════════════════════════════════════
    with tab_llm:
        st.markdown("#### 🤖 LLM Insights")

        if not use_llm:
            st.markdown(
                "<div class='box box-warn'>LLM Insights are disabled. "
                "Enable <b>Enable LLM Insights</b> in the sidebar and re-solve.</div>",
                unsafe_allow_html=True)

        elif llm_result is None:
            st.markdown(
                "<div class='box box-warn'>LLM result unavailable — "
                "the LLM call may have failed. Check your API key.</div>",
                unsafe_allow_html=True)

        else:
            st.markdown("##### Natural Language Explanation")
            st.markdown(
                f"<div class='box box-info'>{llm_result.natural_language_explanation}</div>",
                unsafe_allow_html=True)

            st.divider()

            st.markdown("##### Physical Interpretation")
            st.markdown(
                f"<div class='box box-ok'>{llm_result.physical_interpretation}</div>",
                unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════
    # TAB 3 — Technical Details
    # ══════════════════════════════════════════════════════════════════
    with tab_tech:
        st.markdown("#### 🔧 Technical Details")

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Equation Information**")
            st.json({
                "Equation":      result.get("display_name", "—"),
                "Order":         classification.get("order", "—"),
                "Linear":        classification.get("linear", "—"),
                "Homogeneous":   classification.get("homogeneous", "—"),
                "Family":        classification.get("family", "—"),
            })

        with c2:
            st.markdown("**Solver Information**")
            st.json({
                "Method key":        key,
                "Stiffness detected":routing_decision.stiffness_detected,
                "Equation family":   routing_decision.equation_family,
                "Reason":            routing_decision.reason,
                "Compute time (ms)": round(result["compute_ms"], 2),
            })

        # Raw data preview (numerical methods only)
        if result["t"] is not None and result["y"] is not None:
            st.divider()
            st.markdown("**Solution Array Info**")
            st.json({
                "Time points":     int(len(result["t"])),
                "Time range":      f"[{result['t'][0]:.2f}, {result['t'][-1]:.2f}]",
                "State dimensions":int(result["y"].shape[0]),
            })

            with st.expander("📋 Raw data — first 10 time points"):
                df_data = {"t": result["t"][:10], "x": result["y"][0][:10]}
                if result["y"].shape[0] > 1:
                    df_data["dx/dt"] = result["y"][1][:10]
                st.dataframe(pd.DataFrame(df_data),
                             use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════════
    # TAB 4 — About
    # ══════════════════════════════════════════════════════════════════
    with tab_about:
        st.markdown("#### 📖 About This System")
        st.markdown("""
**Zero Hallucination ODE Solver** — a production-grade solver where every
number is computed by a verified library, never by an AI model.

---

### Architecture
```
User Input
    ↓
Parser  (regex, deterministic)
    ↓
Router  (rule-based logic)
    ↓
Solver  (SymPy / SciPy / Euler)
    ↓
Visualisation  (Matplotlib)
    ↓
Explanation  (LLM — interpretation only, no computation)
```

---

### Available Methods

| Method | Type | Best for |
|---|---|---|
| Symbolic (SymPy) | Exact | Linear constant-coefficient ODEs |
| Laplace Transform | Exact | Linear ODEs — s-domain approach |
| RK45 | Numerical | General non-stiff problems |
| Radau | Numerical | Stiff systems |
| Forward Euler | Educational | Understanding numerical error |
| Improved Euler (Heun's) | Educational | Better than Forward Euler |
| Compare All | — | See all methods side by side |

---

### Supported Notation

| You type | Meaning |
|---|---|
| `x''` | Second derivative |
| `x'` | First derivative |
| `dx/dt` | First derivative (alternative) |
| `x**2` or `x^2` | x squared |
| `sin(t)`, `cos(t)`, `exp(t)` | Standard functions |

---

### Zero Hallucination Guarantee

- **SymPy** — symbolic mathematics
- **SciPy** — numerical integration (`solve_ivp`)
- **NumPy** — array operations
- **Matplotlib** — visualisation

The LLM only generates human-readable *explanations*. It never computes
a single number.

---

**Built with:** Python · Streamlit · SymPy · SciPy · NumPy · Matplotlib
        """)


# ══════════════════════════════════════════════════════════════════════════════
#  RENDER HELPERS — Compare All
# ══════════════════════════════════════════════════════════════════════════════

def _compare_overlay_plot(results: List[Dict]):
    """All successful solutions on one figure (time + phase)."""
    ok = [r for r in results if r["success"] and r["t"] is not None]
    if not ok:
        st.warning("No successful solutions to overlay.")
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor("#fafafa")

    for r in ok:
        t, y, col, name = r["t"], r["y"], r["color"], r["display_name"]
        axes[0].plot(t, y[0], color=col, lw=1.8, label=name, alpha=0.85)
        if y.shape[0] > 1:
            axes[1].plot(y[0], y[1], color=col, lw=1.4, label=name, alpha=0.75)

    for ax, xlabel, ylabel, title in [
        (axes[0], "t",  "x(t)", "Overlapping x(t) — All Methods"),
        (axes[1], "x",  "x′",   "Phase Portrait — All Methods"),
    ]:
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_ylabel(ylabel, fontsize=11)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.legend(fontsize=8, framealpha=0.6)
        ax.grid(True, alpha=0.25)
        ax.set_facecolor("#ffffff")

    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def _compare_stats_table(results: List[Dict]):
    """Side-by-side accuracy stats for all methods."""
    rows = []
    for r in results:
        s = r["stats"]
        rows.append({
            "Method":       r["display_name"],
            "Status":       "✅" if r["success"] else "❌",
            "x final":      f"{s['x_final']:.6f}"  if "x_final" in s else "—",
            "x max":        f"{s['x_max']:.6f}"    if "x_max"   in s else "—",
            "x min":        f"{s['x_min']:.6f}"    if "x_min"   in s else "—",
            "x mean":       f"{s['x_mean']:.6f}"   if "x_mean"  in s else "—",
            "Compute (ms)": f"{r['compute_ms']:.1f}",
        })
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)


def _compare_timing_chart(results: List[Dict]):
    """Horizontal bar chart of computation times."""
    names  = [r["display_name"] for r in results]
    times  = [r["compute_ms"]   for r in results]
    colors = [r["color"]        for r in results]

    fig, ax = plt.subplots(figsize=(8, max(2, len(names) * 0.55 + 0.8)))
    bars = ax.barh(names, times, color=colors, alpha=0.82, height=0.5)
    ax.bar_label(bars, fmt="%.1f ms", padding=5, fontsize=9)
    ax.set_xlabel("Compute time (ms)", fontsize=10)
    ax.set_title("Computation Time per Method", fontsize=11, fontweight="bold")
    ax.grid(axis="x", alpha=0.25)
    ax.set_facecolor("#ffffff")
    fig.patch.set_facecolor("#fafafa")
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


def render_compare_all(results: List[Dict]):
    """Full comparison view."""
    n_ok = sum(1 for r in results if r["success"])
    st.markdown(
        f"### Compare All Methods "
        f"<span class='mbadge mb-cmp'>{n_ok}/{len(results)} succeeded</span>",
        unsafe_allow_html=True)

    tab_ov, tab_st, tab_tm, *method_tabs = st.tabs(
        ["📈 Overlapping Plots", "📊 Stats Table", "⏱ Compute Time"]
        + [("✅ " if r["success"] else "❌ ") + r["display_name"].split("—")[0].strip()
           for r in results]
    )

    with tab_ov:
        st.markdown("#### All solutions overlaid on the same axes")
        _compare_overlay_plot(results)

    with tab_st:
        st.markdown("#### Side-by-side accuracy statistics")
        _compare_stats_table(results)

    with tab_tm:
        st.markdown("#### Wall-clock compute time per method")
        _compare_timing_chart(results)

    for tab, result in zip(method_tabs, results):
        with tab:
            if not result["success"]:
                st.markdown(
                    f"<div class='box box-err'>❌ {result['message']}</div>",
                    unsafe_allow_html=True)
                continue
            _plot_single(result)
            _stat_cards(result["stats"])
            steps = result.get("steps", [])
            sol   = result.get("solution_obj")
            if result["key"] in ("symbolic", "laplace") and steps:
                with st.expander("Step-by-Step Derivation"):
                    _render_symbolic_steps(steps)
            elif result["key"].startswith("euler") and isinstance(steps, list) and steps and isinstance(steps[0], dict):
                with st.expander("Integration Steps (first 10)"):
                    _render_euler_table(steps, sol)


# ══════════════════════════════════════════════════════════════════════════════
#  WELCOME SCREEN
# ══════════════════════════════════════════════════════════════════════════════

def render_welcome():
    st.markdown("""
    <div class="box box-info">
        <h3 style="margin:0 0 6px">👋 Welcome!</h3>
        Enter an ODE in the sidebar, choose a <b>solving method</b>, then click
        <b>Solve ODE</b>. Pick <em>Compare All Methods</em> to run every solver
        and see results side by side.
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### 🧮 Method Guide
        | Method | Type | Best for |
        |---|---|---|
        | Symbolic | Exact | Linear ODEs, teaching |
        | Laplace | Exact | Linear + IC, s-domain |
        | RK45 | Numerical | General non-stiff |
        | Radau | Numerical | Stiff systems |
        | Forward Euler | Educational | Seeing error grow |
        | Improved Euler | Educational | Better than Fwd Euler |
        """)
    with col2:
        st.markdown("""
        ### 💡 Tips
        - **Linear equations** → try Symbolic + Laplace, compare exact solutions
        - **Nonlinear** → Symbolic/Laplace auto-disabled, use RK45 or Radau
        - **Stiff** (large coefficients, e.g. 1000·x') → Radau wins
        - **Learning** → Forward vs Improved Euler shows how step size matters
        - **Compare All** → see every method at once with an overlay plot
        """)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # Header
    st.markdown("""
    <div class="ode-hero">
        <h1>∫ ODE Solver System</h1>
        <p>ZERO HALLUCINATION · MULTI-METHOD · STEP-BY-STEP</p>
    </div>""", unsafe_allow_html=True)

    params = render_sidebar()

    if params["solve"]:
        eq          = params["equation"]
        ic          = params["ic"]
        time_span   = params["time_span"]
        label       = params["method_label"]
        key, _, _   = METHOD_OPTIONS[label]
        use_llm     = params["use_llm"]

        # Parse once
        components = st.session_state.parser.parse(eq, ic)
        router     = ODERouter()
        decision   = router.route(components, time_span)

        classification = {
            "order":       components.order,
            "linear":      components.is_linear,
            "homogeneous": components.is_homogeneous,
            "family":      decision.equation_family,
            "stiff":       decision.stiffness_detected,
        }

        # Guard: linear-only methods on nonlinear equation
        if key in LINEAR_ONLY and not components.is_linear:
            st.error(
                f"**{label.strip()}** only works for linear ODEs. "
                "Your equation contains nonlinear terms. "
                "Please choose RK45, Radau, or an Euler method."
            )
            return

        if key == "compare":
            keys_to_run = _all_method_keys(components)
            display_map = {v[0]: k for k, v in METHOD_OPTIONS.items()}

            with st.spinner("Running all methods…"):
                results = []
                for k in keys_to_run:
                    dname = display_map.get(k, k).split("—")[0].strip()
                    results.append(_run_one(k, components, ic, time_span, dname))

            st.session_state.compare_results = results
            st.session_state.result = None
            st.session_state["_classification"] = classification
            st.session_state["_decision"]       = decision
            st.session_state["_use_llm"]        = use_llm

        else:
            dname = label.split("—")[0].strip()
            with st.spinner(f"Solving with {dname}…"):
                result = _run_one(key, components, ic, time_span, dname)

            llm_result = None
            if use_llm:
                try:
                    enhanced = st.session_state.llm_solver.solve_with_explanation(
                        equation=eq, initial_conditions=ic, time_span=time_span)
                    llm_result = enhanced
                except Exception:
                    pass

            st.session_state.result           = result
            st.session_state.compare_results  = None
            st.session_state["_classification"] = classification
            st.session_state["_decision"]       = decision
            st.session_state["_use_llm"]        = use_llm
            st.session_state["_llm_result"]     = llm_result

        st.success("✅ Done!")

    # ── Display ───────────────────────────────────────────────────────
    classification = st.session_state.get("_classification", {})
    decision       = st.session_state.get("_decision")
    use_llm        = st.session_state.get("_use_llm", False)

    if st.session_state.compare_results is not None:
        render_compare_all(st.session_state.compare_results)

    elif st.session_state.result is not None:
        llm_result = st.session_state.get("_llm_result")
        render_single_method(
            st.session_state.result,
            classification,
            decision,
            use_llm,
            llm_result
        )

    else:
        render_welcome()


if __name__ == "__main__":
    main()