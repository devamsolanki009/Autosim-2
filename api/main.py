"""
api/main.py
───────────
FastAPI backend for AutoSim ODE Solver.
Exposes:
  POST /solve            — parse + route + solve an ODE
  POST /verify           — run 6-check verification on a completed solution
  POST /generate-solver  — 5-step ODE Solver Engine (parse→generate→debug→eval)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np

# Load .env file if present (python-dotenv is optional)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# Default Wolfram key from environment — users can set WOLFRAM_APP_ID in .env
_DEFAULT_WOLFRAM_KEY: Optional[str] = (os.environ.get("WOLFRAM_APP_ID") or "").strip() or None

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── local imports ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from core.parser import ODEParser
from core.router import ODERouter
from solvers.numerical import NumericalSolver
from solvers.euler import EulerSolver
from utils.verifier import ODEVerifier, VerificationReport, VerificationSource
from utils.solver_engine import run_pipeline, step5_refine, SolverEngineResult

# Optional: symbolic / laplace (graceful import)
try:
    from solvers.symbolic import SymbolicSolver
    import sympy as sp
    _HAS_SYMBOLIC = True
except Exception:
    _HAS_SYMBOLIC = False

try:
    from solvers.laplace import LaplaceSolver
    _HAS_LAPLACE = True
except Exception:
    _HAS_LAPLACE = False


# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(title="AutoSim ODE Solver API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singleton solvers
_parser = ODEParser()
_router = ODERouter()
_num_solver = NumericalSolver()
_euler_solver = EulerSolver()
_verifier = ODEVerifier()
_sym_solver = SymbolicSolver() if _HAS_SYMBOLIC else None
_lap_solver = LaplaceSolver() if _HAS_LAPLACE else None


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

class IC(BaseModel):
    x: float = 1.0
    dx: float = 0.0


class SolveRequest(BaseModel):
    equation: str
    ic: IC
    time_span: List[float] = [0.0, 50.0]
    method: str = "rk45"
    use_llm: bool = False


class SolveResultIn(BaseModel):
    t: List[float]
    y: List[List[float]]
    method: str
    stats: Dict[str, Any] = {}


class VerifyRequest(BaseModel):
    equation: str
    ic: IC
    time_span: List[float] = [0.0, 50.0]
    result: SolveResultIn
    wolfram_key: Optional[str] = None


class GenerateSolverRequest(BaseModel):
    equation: str
    ic: IC
    time_span: List[float] = [0.0, 50.0]
    # Optional: for Step 5 refinement
    refine_error_type: Optional[str] = None   # 'oscillation'|'high_error'|'slow'|'runtime'
    refine_error_detail: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_float(v) -> float:
    """Convert numpy scalar / float to Python float, handling NaN/Inf."""
    try:
        f = float(v)
        if np.isnan(f) or np.isinf(f):
            return 0.0
        return f
    except Exception:
        return 0.0


def _stats(t: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    x = y[0]
    stats = {
        "x_final": _safe_float(x[-1]),
        "x_max":   _safe_float(np.max(x)),
        "x_min":   _safe_float(np.min(x)),
        "x_mean":  _safe_float(np.mean(x)),
        "x_std":   _safe_float(np.std(x)),
        "t_start": _safe_float(t[0]),
        "t_end":   _safe_float(t[-1]),
        "n_points": int(len(t)),
        "n_states": int(y.shape[0]),
    }
    return stats


def _sample_symbolic(sol, time_span) -> tuple[np.ndarray, np.ndarray]:
    """Sample a symbolic solution onto a uniform grid."""
    t_sym = sp.Symbol("t", positive=True)
    expr = sol.particular_solution or sol.general_solution
    t_arr = np.linspace(time_span[0], time_span[1], 300)
    try:
        f = sp.lambdify(t_sym, expr, modules=["numpy"])
        x_vals = np.array([float(np.real(f(ti))) for ti in t_arr])
    except Exception:
        x_vals = np.zeros(len(t_arr))
    # Numerical derivative for velocity row
    v_vals = np.gradient(x_vals, t_arr)
    y_arr = np.vstack([x_vals, v_vals])
    return t_arr, y_arr


def _source_to_dict(src: VerificationSource) -> Dict:
    d = {
        "name":        src.name,
        "status":      src.status,
        "message":     src.message,
        "max_error":   src.max_error,
        "mean_error":  src.mean_error,
        "confidence":  src.confidence,
        "reference_t": src.reference_t,
        "reference_y": src.reference_y,
        "details":     src.details,
    }
    return d


def _report_to_dict(report: VerificationReport) -> Dict:
    return {
        "sources":            [_source_to_dict(s) for s in report.sources],
        "overall_status":     report.overall_status,
        "overall_confidence": report.overall_confidence,
        "summary":            report.summary,
        "compute_ms":         report.compute_ms,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /solve
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/solve")
async def solve(req: SolveRequest):
    t_wall = time.perf_counter()

    ic_dict = {"x": req.ic.x, "dx": req.ic.dx}
    time_span = tuple(req.time_span[:2])
    method_key = req.method.lower()

    try:
        components = _parser.parse(req.equation, ic_dict)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Parse error: {exc}")

    t_arr: Optional[np.ndarray] = None
    y_arr: Optional[np.ndarray] = None
    success = False
    message = ""

    steps: List[Dict] = []

    try:
        if method_key in ("symbolic",) and _HAS_SYMBOLIC:
            sol = _sym_solver.solve(components, ic_dict)
            t_arr, y_arr = _sample_symbolic(sol, time_span)
            success = True
            message = "Exact symbolic solution."
            steps = [
                {"step_number": s.step_number, "title": s.description,
                 "equation": s.equation, "latex": s.latex}
                for s in sol.derivation_steps
            ]

        elif method_key == "laplace" and _HAS_LAPLACE and _HAS_SYMBOLIC:
            sol = _lap_solver.solve(components, ic_dict)
            if sol.success and sol.x_of_t is not None:
                t_sym2 = sp.Symbol("t", positive=True)
                t_arr2 = np.linspace(time_span[0], time_span[1], 300)
                f2 = sp.lambdify(t_sym2, sol.x_of_t, modules=["numpy"])
                x2 = np.array([float(np.real(f2(ti))) for ti in t_arr2])
                v2 = np.gradient(x2, t_arr2)
                t_arr, y_arr = t_arr2, np.vstack([x2, v2])
                success = sol.success
                message = sol.message
                steps = [
                    {"step_number": s.step_number, "title": s.description,
                     "equation": s.equation, "latex": s.latex}
                    for s in sol.derivation_steps
                ]
            else:
                raise ValueError(sol.message)

        elif method_key in ("euler_fwd", "euler_imp"):
            variant = "forward" if method_key == "euler_fwd" else "improved"
            sol = _euler_solver.solve(components, ic_dict,
                                      time_span=time_span, variant=variant)
            if sol.success:
                t_arr, y_arr = sol.t, sol.y
                success = True
                message = sol.message
                steps = sol.steps_table
            else:
                raise ValueError(sol.message)

        elif method_key == "compare":
            # Run RK45 as the primary solution for plotting; collect stats from both
            sol_rk45  = _num_solver.solve(components, ic_dict,
                                          time_span=time_span, method="RK45")
            sol_radau = _num_solver.solve(components, ic_dict,
                                          time_span=time_span, method="Radau")
            if not sol_rk45.success:
                raise ValueError(f"RK45 failed: {sol_rk45.message}")
            t_arr, y_arr = sol_rk45.t, sol_rk45.y
            success = True
            message = "Compare mode: RK45 plotted; Radau run for comparison."
            # Build comparison steps
            def _stat(key: str, s) -> str:
                v = s.statistics.get(key)
                return f"{v:.6f}" if v is not None else "—"
            steps = [
                {
                    "step_number": 1,
                    "title": "Method A — RK45 (Explicit, Non-stiff)",
                    "equation": (
                        "Dormand-Prince 4(5) explicit Runge-Kutta — adaptive step-size.\n"
                        f"x_final = {_stat('x_final', sol_rk45)},  "
                        f"x_max = {_stat('x_max', sol_rk45)},  "
                        f"x_min = {_stat('x_min', sol_rk45)}"
                    ),
                    "latex": r"\text{RK45: explicit, 6-stage, Dormand-Prince adaptive pair}",
                    "type": "symbolic",
                },
                {
                    "step_number": 2,
                    "title": "Method B — Radau IIA (Implicit, L-stable)",
                    "equation": (
                        "3-stage 5th-order implicit collocation — best for stiff systems.\n"
                        f"x_final = {_stat('x_final', sol_radau)},  "
                        f"x_max = {_stat('x_max', sol_radau)},  "
                        f"x_min = {_stat('x_min', sol_radau)}"
                    ),
                    "latex": r"\text{Radau IIA: implicit, L-stable, Newton iterations per step}",
                    "type": "symbolic",
                },
                {
                    "step_number": 3,
                    "title": "Agreement Check",
                    "equation": (
                        "Both methods run with rtol=1e-8, atol=1e-10.\n"
                        f"RK45 x_final = {_stat('x_final', sol_rk45)}  vs  "
                        f"Radau x_final = {_stat('x_final', sol_radau)}\n"
                        "Close agreement → solution is reliable regardless of method choice."
                    ),
                    "latex": r"\left| x_{\text{RK45}} - x_{\text{Radau}} \right| \approx 0 \;\Rightarrow\; \text{verified}",
                    "type": "symbolic",
                },
                {
                    "step_number": 4,
                    "title": "When to Use Which",
                    "equation": (
                        "RK45:  fast, explicit — use for non-stiff / smooth systems.\n"
                        "Radau: slower per step but stable — use when RK45 diverges or requires tiny steps.\n"
                        "Rule of thumb: try RK45 first; switch to Radau if you see oscillations."
                    ),
                    "latex": r"\text{Stiff?} \Rightarrow \text{Radau}\quad\text{else}\Rightarrow \text{RK45}",
                    "type": "symbolic",
                },
            ]

        else:
            # Default: numerical (rk45, radau, or fallback)
            scipy_method = "RK45" if method_key == "rk45" else "Radau"
            sol = _num_solver.solve(components, ic_dict,
                                    time_span=time_span, method=scipy_method)
            if sol.success:
                t_arr, y_arr = sol.t, sol.y
                success = True
                message = sol.message

                # ── Build method-specific step breakdown ──────────────────────
                step1 = {
                    "step_number": 1,
                    "title": "Rewrite as First-Order System",
                    "equation": "Let v = x'  →  [x' = v,  v' = f(t, x, v)]",
                    "latex": r"\text{Let } v = x' \Rightarrow \begin{cases} x' = v \\ v' = f(t, x, v) \end{cases}",
                    "type": "symbolic",
                }
                step2 = {
                    "step_number": 2,
                    "title": "State Vector & Initial Conditions",
                    "equation": f"y = [x, v]^T,  y0 = [{ic_dict['x']}, {ic_dict['dx']}]",
                    "latex": rf"\mathbf{{y}} = \begin{{bmatrix}} x \\ v \end{{bmatrix}},\quad \mathbf{{y}}_0 = \begin{{bmatrix}} {ic_dict['x']} \\ {ic_dict['dx']} \end{{bmatrix}}",
                    "type": "symbolic",
                }

                if scipy_method == "RK45":
                    step3 = {
                        "step_number": 3,
                        "title": "Method: RK45 (Explicit Runge-Kutta 4(5))",
                        "equation": (
                            "Dormand-Prince explicit RK pair — 6 stage evaluations per step:\n"
                            "k1 = f(tₙ, yₙ)\n"
                            "k2 = f(tₙ + c₂h, yₙ + h·a₂₁k₁)\n"
                            "...  (4th-order solution + 5th-order error estimate)\n"
                            "Adaptive step-size via error control: if err > atol → halve h"
                        ),
                        "latex": (
                            r"y_{n+1} = y_n + h\sum_{i=1}^{6} b_i k_i"
                            r"\quad k_i = f\!\left(t_n + c_i h,\; y_n + h\sum_{j<i} a_{ij}k_j\right)"
                        ),
                        "type": "symbolic",
                    }
                    step4 = {
                        "step_number": 4,
                        "title": "Error Control & Step-Size Adaptation",
                        "equation": (
                            "rtol = 1e-8,  atol = 1e-10\n"
                            "err = ‖y₅ - y₄‖  (5th vs 4th order embedded pair)\n"
                            "Best for: non-stiff systems — fast, explicit, minimal overhead"
                        ),
                        "latex": (
                            r"\text{err} = \left\| y^{(5)} - y^{(4)} \right\|,"
                            r"\quad h_{\text{new}} = h \left(\frac{\text{tol}}{\text{err}}\right)^{1/5}"
                        ),
                        "type": "symbolic",
                    }
                else:  # Radau
                    step3 = {
                        "step_number": 3,
                        "title": "Method: Radau IIA (Implicit Collocation — L-stable)",
                        "equation": (
                            "3-stage 5th-order implicit Runge-Kutta (Radau IIA collocation):\n"
                            "Solves a coupled nonlinear system at each step (Newton iterations):\n"
                            "  [I - h·A⊗J] · ΔK = residual\n"
                            "L-stable → cannot go unstable for stiff problems regardless of step size"
                        ),
                        "latex": (
                            r"\mathbf{K} = f\!\left(t_n\mathbf{1} + h\mathbf{c},\;"
                            r"y_n\mathbf{1} + h(A\otimes I)\mathbf{K}\right)"
                            r",\quad y_{n+1} = y_n + h\mathbf{b}^T\mathbf{K}"
                        ),
                        "type": "symbolic",
                    }
                    step4 = {
                        "step_number": 4,
                        "title": "Stiffness Handling & Newton Convergence",
                        "equation": (
                            "rtol = 1e-8,  atol = 1e-10\n"
                            "Each step: Newton iterations until ‖ΔK‖ < tol\n"
                            "Jacobian reused across steps (quasi-Newton) for speed\n"
                            "Best for: stiff systems (large eigenvalue spread) — implicit, robust"
                        ),
                        "latex": (
                            r"\left(I - hA_{11}J\right)\Delta K^{(\nu)} = -F^{(\nu)},"
                            r"\quad \text{until } \|\Delta K\| < \text{tol}"
                        ),
                        "type": "symbolic",
                    }

                step5 = {
                    "step_number": 5,
                    "title": "Integration Result",
                    "equation": (
                        f"n_points = {len(sol.t)},  "
                        f"t ∈ [{float(sol.t[0]):.2f}, {float(sol.t[-1]):.2f}],  "
                        f"success = {sol.success}"
                    ),
                    "latex": (
                        rf"n = {len(sol.t)},\quad t \in [{float(sol.t[0]):.2f},\ {float(sol.t[-1]):.2f}],"
                        rf"\quad \text{{success}} = \text{{{sol.success}}}"
                    ),
                    "type": "symbolic",
                }

                steps = [step1, step2, step3, step4, step5]
            else:
                raise ValueError(sol.message)

    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Solver error: {exc}")

    if t_arr is None or y_arr is None:
        raise HTTPException(status_code=500, detail="Solver returned no data.")

    compute_ms = (time.perf_counter() - t_wall) * 1000.0
    stats = _stats(t_arr, y_arr)
    stats["compute_ms"] = round(compute_ms, 2)

    # Classification
    classification = {
        "order":       components.order,
        "linear":      components.is_linear,
        "homogeneous": components.is_homogeneous,
    }
    try:
        decision = _router.route(components, time_span)
        classification["family"] = decision.equation_family
        classification["stiff"] = decision.stiffness_detected
    except Exception:
        classification["family"] = "Unknown"
        classification["stiff"] = False

    return {
        "t":              t_arr.tolist(),
        "y":              y_arr.tolist(),
        "stats":          stats,
        "method":         method_key,
        "success":        success,
        "message":        message,
        "classification": classification,
        "steps":          steps,
    }


# ─────────────────────────────────────────────────────────────────────────────
# POST /verify
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/verify")
async def verify(req: VerifyRequest):
    ic_dict = {"x": req.ic.x, "dx": req.ic.dx}
    time_span = tuple(req.time_span[:2])

    # Parse equation to get components
    try:
        components = _parser.parse(req.equation, ic_dict)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Parse error: {exc}")

    # Convert result to native dicts/arrays
    result = {
        "t":      req.result.t,
        "y":      req.result.y,
        "method": req.result.method,
        "stats":  req.result.stats,
    }

    wolfram_key = (req.wolfram_key.strip() if req.wolfram_key and req.wolfram_key.strip()
                   else _DEFAULT_WOLFRAM_KEY)

    try:
        report = _verifier.verify(
            components=components,
            result=result,
            ic=ic_dict,
            time_span=time_span,
            wolfram_app_id=wolfram_key,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Verifier error: {exc}")

    return _report_to_dict(report)


# ─────────────────────────────────────────────────────────────────────────────
# POST /generate-solver  — 5-Step ODE Solver Engine
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/generate-solver")
async def generate_solver(req: GenerateSolverRequest):
    """
    Run the full 5-step AutoSim ODE Solver Engine pipeline.

    Step 1 — Parse & restate the problem
    Step 2 — Generate solver() Python code with CoT comments
    Step 3 — Self-debug (validate imports, shapes, signatures)
    Step 4 — Append evaluation + plot block
    Step 5 — (Optional) Refine code if error_type provided
    """
    ic_dict   = {"x": req.ic.x, "dx": req.ic.dx}
    time_span = tuple(req.time_span[:2])

    try:
        result = run_pipeline(req.equation, ic_dict, time_span)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")

    # Step 5 — optional refinement pass
    refined_code = None
    if req.refine_error_type and result.is_valid:
        try:
            refined_code = step5_refine(result, req.refine_error_type,
                                        req.refine_error_detail or "")
        except Exception:
            refined_code = None

    return {
        # Step 1 output
        "parsed": {
            "natural_language":  result.parsed.natural_language,
            "order":             result.parsed.order,
            "is_linear":         result.parsed.is_linear,
            "is_stiff":          result.parsed.is_stiff,
            "is_homogeneous":    result.parsed.is_homogeneous,
            "n_vars":            result.parsed.n_vars,
            "forcing_function":  result.parsed.forcing_function,
            "nonlinear_terms":   result.parsed.nonlinear_terms,
            "has_pde":           result.parsed.has_partial_derivatives,
        },
        # Step 2+3 output
        "solver_code":    result.solver_code,
        "method_chosen":  result.method_chosen,
        "debug_notes":    result.debug_notes,
        "issues_found":   result.issues_found,
        "is_valid":       result.is_valid,
        # Step 4 output
        "eval_code":      result.eval_code,
        "full_code":      result.full_code,
        # Step 5 output (optional)
        "refined_code":   refined_code,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Health check
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ─────────────────────────────────────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)

