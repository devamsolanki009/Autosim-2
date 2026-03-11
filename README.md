# AutoSim — AI-Powered Differential Equation Solver

> A full-stack scientific computing platform that combines a Python numerical/symbolic solver backend with a modern Next.js frontend and LLM-powered explanations via Ollama.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Full Project Structure](#3-full-project-structure)
4. [Technology Stack](#4-technology-stack)
5. [Backend — Python (AutoSim-2)](#5-backend--python-autosim-2)
6. [Frontend — Next.js](#6-frontend--nextjs)
7. [API Contract](#7-api-contract)
8. [Data Flow — End to End](#8-data-flow--end-to-end)
9. [Installation & Setup](#9-installation--setup)
10. [Running the Project](#10-running-the-project)
11. [Environment Variables](#11-environment-variables)
12. [Features](#12-features)
13. [Supported Equation Types & Examples](#13-supported-equation-types--examples)
14. [Solver Selection Logic](#14-solver-selection-logic)
15. [Adding a New Solver](#15-adding-a-new-solver)
16. [Adding a New PDE / Equation Type](#16-adding-a-new-pde--equation-type)
17. [Extending the Frontend](#17-extending-the-frontend)
18. [Connecting to a Different LLM](#18-connecting-to-a-different-llm)
19. [Common Issues & Fixes](#19-common-issues--fixes)
20. [npm Command Reference](#20-npm-command-reference)

---

## 1. Project Overview

AutoSim is a two-part system:

**Backend (Python):** A scientific computing engine called `AutoSim-2` that can parse ordinary and partial differential equations, route them to the most suitable solver, compute solutions numerically or symbolically, and optionally generate natural-language explanations using a locally running LLM.

**Frontend (Next.js):** A dark-theme, terminal-aesthetic web application that lets users type equations (or describe them in plain English), configure solver parameters, run simulations, and explore results through interactive Plotly charts, a metrics dashboard, an LLM explanation panel, and a timestamped run log.

The two parts communicate through `backend_api.py` — a FastAPI server that wraps the existing AutoSim Python modules into REST endpoints.

### What you can do with AutoSim

- Solve first-order, second-order, and coupled systems of ODEs
- Solve PDEs using numerical methods
- Get exact closed-form solutions via symbolic or Laplace transform solvers
- Describe your problem in plain English and have it converted to an equation automatically
- Visualise solutions as time series, phase portraits, or heatmaps with Plotly
- Get a step-by-step explanation of the math and solver choice from Llama3 via Ollama
- Export the run log as JSON

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                             │
│                                                                 │
│   http://localhost:3000  (Next.js App Router)                   │
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────────────────────┐  │
│  │   InputPanel     │    │        ResultsPanel              │  │
│  │  (left sidebar)  │    │  ┌──────┬────────┬───────┬─────┐ │  │
│  │                  │    │  │ Plot │ Soln   │Explain│ Log │ │  │
│  │ • equation input │    │  │      │ Panel  │ Panel │     │ │  │
│  │ • method picker  │    │  └──────┴────────┴───────┴─────┘ │  │
│  │ • time range     │    │                                  │  │
│  │ • IC / params    │    └──────────────────────────────────┘  │
│  │ • examples       │                                          │
│  └────────┬─────────┘                                          │
│           │  onClick → handleSolve()                           │
│           ▼                                                     │
│       page.tsx  (AppState orchestrator)                        │
│           │  fetch POST /solve                                  │
└───────────┼─────────────────────────────────────────────────────┘
            │  HTTP  (localhost:8000)
            ▼
┌─────────────────────────────────────────────────────────────────┐
│               backend_api.py  (FastAPI)                         │
│                                                                 │
│   POST /solve ──► parse_ode() ──► route_solver()               │
│                       │                                         │
│              ┌────────┴──────────────────────────┐             │
│              │  Solver dispatch                   │             │
│              │  ┌──────────┐  ┌────────────────┐ │             │
│              │  │ euler.py │  │ numerical.py   │ │             │
│              │  │ (Euler)  │  │ (RK4/SciPy)    │ │             │
│              │  └──────────┘  └────────────────┘ │             │
│              │  ┌──────────┐  ┌────────────────┐ │             │
│              │  │symbolic  │  │ laplace.py     │ │             │
│              │  │ .py      │  │ (transforms)   │ │             │
│              │  └──────────┘  └────────────────┘ │             │
│              └───────────────────────────────────┘             │
│                       │                                         │
│              Optional: EnhancedSolver (LLM explain)            │
│                       │  Ollama HTTP  (localhost:11434)         │
│                       ▼                                         │
│                   Llama3 / DeepSeek Coder                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Full Project Structure

```
AutoSim-2/                          ← your existing Python backend root
├── backend_api.py                  ← NEW: FastAPI bridge (place here)
├── app.py                          ← original Streamlit entry point
├── main.py                         ← original CLI entry point
├── core/
│   ├── parser.py                   ← equation string → AST / sympy expr
│   └── router.py                   ← decides which solver to use
├── solvers/
│   ├── euler.py                    ← Forward Euler integrator
│   ├── numerical.py                ← RK4 / SciPy odeint
│   ├── symbolic.py                 ← SymPy exact solver
│   └── laplace.py                  ← Laplace transform solver
├── llm_integration/
│   ├── enhanced_solver.py          ← wraps solver + generates explanation
│   ├── nl_pde_parser.py            ← natural language → equation (Ollama)
│   └── deepseek_interface.py       ← DeepSeek Coder LLM client
└── utils/
    └── visualization.py            ← matplotlib helpers (Streamlit era)

autosim-frontend/                   ← NEW: Next.js frontend
├── README.md                       ← this file
├── package.json                    ← Node.js dependencies
├── tsconfig.json                   ← TypeScript config
├── tailwind.config.ts              ← Tailwind + custom design tokens
├── postcss.config.mjs              ← PostCSS config
├── next.config.mjs                 ← Next.js config
├── .env.local                      ← backend URL env var
│
├── src/
│   ├── app/
│   │   ├── layout.tsx              ← root layout: fonts, metadata
│   │   ├── page.tsx                ← MAIN ORCHESTRATOR: state, API calls
│   │   ├── globals.css             ← Tailwind directives + animations
│   │   └── api/health/route.ts     ← optional Next.js proxy health check
│   │
│   ├── components/
│   │   ├── StatusBar.tsx           ← pipeline stage indicator (top bar)
│   │   ├── InputPanel.tsx          ← left sidebar: all input controls
│   │   ├── ResultsPanel.tsx        ← right area: tabs + loading states
│   │   ├── PlotPanel.tsx           ← Plotly interactive charts
│   │   ├── SolutionPanel.tsx       ← metrics, values, convergence
│   │   ├── ExplanationPanel.tsx    ← formatted LLM explanation
│   │   └── LogPanel.tsx            ← timestamped run log + JSON export
│   │
│   ├── lib/
│   │   ├── api.ts                  ← fetch wrappers: solveODE, healthCheck
│   │   └── examples.ts             ← 5 preset examples with full configs
│   │
│   └── types/
│       └── index.ts                ← all TypeScript interfaces
```

---

## 4. Technology Stack

### Backend

| Component | Technology | Purpose |
|---|---|---|
| API Server | FastAPI + Uvicorn | REST endpoints, CORS, hot reload |
| ODE Parser | `core/parser.py` + SymPy | Converts equation strings to structured form |
| Solver Router | `core/router.py` | Deterministic rule-based solver selection |
| Numerical Solver | SciPy `odeint` / custom RK4 | Forward integration of ODEs |
| Euler Solver | Custom NumPy | Fast first-order integration |
| Symbolic Solver | SymPy `dsolve` | Exact closed-form solutions |
| Laplace Solver | SymPy transforms | Laplace method for linear ODEs |
| LLM (explanation) | Ollama + Llama3 | Natural language explanation of solutions |
| LLM (NL input) | Ollama + Llama3 / DeepSeek | Plain English → equation conversion |

### Frontend

| Component | Technology | Purpose |
|---|---|---|
| Framework | Next.js 14 (App Router) | Server/client components, routing |
| Language | TypeScript | Type safety across all components |
| Styling | Tailwind CSS v3 + custom tokens | Utility-first styling |
| Charts | Plotly.js + react-plotly.js | Interactive scientific plots |
| Icons | lucide-react | Consistent icon set |
| HTTP client | Native `fetch` | No extra library needed |

---

## 5. Backend — Python (AutoSim-2)

### 5.1 Core Modules

#### `core/parser.py` — Equation Parser

Takes a raw equation string from the user and converts it to a structured representation usable by the solvers. It handles:

- Single first-order ODEs: `dy/dt = -k*y`
- Second-order ODEs written as `d2x/dt2 + omega^2*x = 0`
- Systems of coupled ODEs separated by semicolons: `dx/dt = alpha*x - beta*x*y; dy/dt = delta*x*y - gamma*y`
- Standard math operators and constants

```python
# Example usage
from core.parser import parse_ode
parsed = parse_ode("dy/dt = -k*y")
```

#### `core/router.py` — Solver Router

Deterministically decides which solver to use based on properties of the parsed equation:

| Equation Property | Chosen Solver |
|---|---|
| Linear ODE with constant coefficients | `laplace` or `symbolic` |
| Nonlinear ODE | `numerical` (RK4) |
| Stiff ODE (large eigenvalue ratio) | `numerical` with implicit stepping |
| Simple first-order | `euler` (fast) |
| User-specified | honours the user's choice |

```python
from core.router import route_solver
method = route_solver(parsed_equation)  # returns "euler" | "runge_kutta" | etc.
```

### 5.2 Solvers

All solvers share the same calling convention used by `backend_api.py`:

```python
result = solve_*(parsed_eq, t_array, initial_conditions={...}, parameters={...})
```

They return either a `dict` with keys `t`, `y`, `variables` (optionally `solution_expression`) or a `(t, y)` tuple. The bridge normalizes both shapes.

#### `solvers/euler.py` — Forward Euler

Implements the classic explicit Euler method:

```
y[n+1] = y[n] + dt * f(t[n], y[n])
```

Fast and simple. Suitable for non-stiff problems with small `dt`. First-order accurate (error ∝ dt).

#### `solvers/numerical.py` — RK4 / SciPy

Uses fourth-order Runge-Kutta or SciPy's `odeint` (which uses LSODA internally and auto-switches between stiff/non-stiff methods). This is the default solver for most problems. Fourth-order accurate (error ∝ dt⁴).

#### `solvers/symbolic.py` — SymPy Exact Solver

Calls SymPy's `dsolve()` to find a closed-form analytical solution. Works for:
- Linear ODEs with constant coefficients
- Separable ODEs
- Bernoulli equations
- Exact equations

Returns a `solution_expression` string (e.g. `y(t) = C1*exp(-k*t)`) in addition to numerical values.

#### `solvers/laplace.py` — Laplace Transform Solver

Applies the Laplace transform method, solving in the frequency domain and inverting back. Particularly well-suited for:
- Initial value problems with constant coefficients
- Systems with piecewise forcing functions
- Step/impulse inputs

### 5.3 LLM Integration

Located in the `llm_integration/` folder. Connects to a locally running Ollama server.

#### `enhanced_solver.py` — Explanation Generator

After a solution is computed, this module sends the equation, solver choice, and solution statistics to Llama3 with a structured prompt, and returns a natural-language explanation covering:
- Mathematical interpretation of the equation
- Physical meaning of the solution behaviour
- Why the chosen solver was appropriate
- Key characteristics of the solution curve

#### `nl_pde_parser.py` — Natural Language → Equation

When the user selects "Natural Language" input mode, this module sends the user's prose description to Llama3 or DeepSeek and extracts:
- The governing equation in standard notation
- Initial conditions
- Parameter values

Example:
```
Input:  "A spring-mass system with mass 2kg, spring constant 8 N/m, starting at 3m displacement"
Output: { equation: "d2x/dt2 + 4*x = 0", initial_conditions: {x: 3, "dx/dt": 0}, parameters: {} }
```

#### `deepseek_interface.py` — DeepSeek Coder Client

An alternative LLM backend (DeepSeek Coder via Ollama) for more technical equation parsing. Can be swapped for Llama3 by changing the model name in the Ollama call.

### 5.4 FastAPI Bridge (`backend_api.py`)

This is the file you add to your `AutoSim-2/` root. It wraps all the existing Python modules into a clean REST API.

#### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Returns backend status, autosim availability, LLM availability |
| `GET` | `/solvers` | Lists all available solver method names |
| `POST` | `/solve` | Main endpoint — solves an ODE and returns results |

#### How the bridge calls your modules

```
POST /solve
  │
  ├─ if input_mode == "natural_language"
  │    └─ NLPDEParser().parse(equation)  → structured equation
  │
  ├─ parse_ode(equation_str)             → parsed representation
  │
  ├─ if method == "auto"
  │    └─ route_solver(parsed_eq)        → method name
  │
  ├─ dispatch to solver:
  │    "euler"       → solve_euler(...)
  │    "runge_kutta" → solve_numerical(...)
  │    "numerical"   → solve_numerical(...)
  │    "symbolic"    → solve_symbolic(...)
  │    "laplace"     → solve_laplace(...)
  │
  ├─ normalize output to { t, y, variables, solution_expression }
  │
  ├─ if explain == true
  │    └─ EnhancedSolver().explain(...)  → explanation string
  │
  └─ return SolveResponse JSON
```

#### Output normalisation

Your solvers may return output in different shapes. The bridge handles all of them:

```python
# Dict output
if isinstance(raw, dict):
    t_list = raw.get("t", t_arr).tolist()
    y_raw  = raw.get("y", [])
    var_names = raw.get("variables", ...)

# Tuple output
elif isinstance(raw, tuple):
    t_out, y_out = raw[0], raw[1]
    ...
```

If your solvers return a different format, edit this block in `backend_api.py` around line 100.

#### CORS

The bridge allows requests from `localhost:3000` and `127.0.0.1:3000`. To allow production domains add them to the `allow_origins` list:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-domain.com"],
    ...
)
```

---

## 6. Frontend — Next.js

### 6.1 `page.tsx` — Orchestrator

The main page is the **single source of truth** for the entire UI. It owns all application state and coordinates every component.

#### State managed by `page.tsx`

```typescript
interface AppState {
  status: AppStatus;          // idle | parsing | routing | solving | explaining | done | error
  result: SolveResult | null; // the full backend response
  logs: LogEntry[];           // timestamped log entries shown in LogPanel
  activeTab: "plot" | "solution" | "explanation" | "log";
}
```

#### `handleSolve()` — the main workflow function

When the user clicks **RUN SIMULATION**, `handleSolve()` executes this sequence:

```
1. Reset state (clear old result and logs)
2. Set status → "parsing"   + add log entries about input
3. Small delay (lets UI re-render to show the parsing stage)
4. Set status → "routing"   + add log entries about method and grid size
5. Set status → "solving"   + call backend API via fetch
6. Await SolveResult from backend
7. If explanation present → set status → "explaining" briefly
8. Set status → "done", save result into state
9. Switch active tab to "plot"
```

This multi-stage approach makes the status bar and log panel feel alive — each stage renders as the simulation progresses, rather than the UI freezing until the whole thing completes.

#### Backend health polling

The page polls `GET /health` every 15 seconds and shows a live online/offline badge in the nav bar. This uses `AbortSignal.timeout(3000)` so a slow backend doesn't block the UI.

### 6.2 Components

#### `StatusBar.tsx`

A top strip that shows the five-stage pipeline as a horizontal sequence of blocks:

```
PARSE ──── ROUTE ──── SOLVE ──── EXPLAIN ──── DONE
```

Each block changes colour based on the current `AppStatus`:
- **Upcoming** → grey, dim border
- **Active** → cyan with glow, pulsing dot
- **Passed** → green

#### `InputPanel.tsx`

The left sidebar. Contains everything the user needs to configure a simulation:

| Control | What it does |
|---|---|
| **Input mode toggle** | Switch between `EQUATION` (math notation) and `NATURAL LANG` (plain English) |
| **Equation/description textarea** | Main input — equation string or prose description |
| **Solver method selector** | 6 buttons: Auto, Runge-Kutta 4, Euler, Symbolic, Laplace, Numerical |
| **Time range** | Three number inputs: T₀, T₁, and Δt |
| **Initial conditions** | JSON textarea — e.g. `{"y": 1.0, "dy/dt": 0.0}` |
| **Parameters** | JSON textarea — e.g. `{"k": 0.5, "omega": 2.0}` |
| **LLM explanation toggle** | Toggle switch to enable/disable Ollama explanation generation |
| **Examples dropdown** | 5 presets that populate all fields instantly |
| **RUN SIMULATION button** | Disabled when loading or equation is empty; shows spinner when active |

#### `ResultsPanel.tsx`

The right-side container that manages the four output tabs. Also renders:
- **Loading skeleton** with shimmer animations during computation
- **Empty state** with example equation hints when no simulation has run
- **Error state** showing the last error log entry when status is `"error"`

#### `PlotPanel.tsx`

An interactive Plotly chart with three view modes switchable via buttons:

| View | When available | What it shows |
|---|---|---|
| **Time Series** | Always | Each variable plotted against time; per-variable colour-coded toggle buttons |
| **Phase Portrait** | 2+ variables | Variable 1 vs Variable 2 with start (green) and end (red) markers |
| **Heatmap** | >20 time steps | All variables as a 2D colour map over time |

The Plotly layout uses the custom dark colour scheme with transparent background, matching the rest of the UI. The `react-plotly.js` component is dynamically imported to avoid SSR issues.

#### `SolutionPanel.tsx`

A dashboard-style panel showing:
- **Status header** with solver type and method used
- **Parsed equation** display (code block)
- **Closed-form solution** (shown only for symbolic/Laplace results)
- **Metrics grid**: solve time, time steps, time span, number of variables
- **Final values table**: initial value, final value, and max absolute value per variable
- **Convergence info**: converged/not-converged, iterations, residual (when available)
- **Warnings list**: any non-fatal issues from the solver

#### `ExplanationPanel.tsx`

Renders the LLM-generated explanation from Ollama. Handles markdown-like structure automatically:
- Lines starting with `#` become styled section headers with a cyan dot
- Lines containing math operators or ∂/∫ symbols get monospace treatment
- Backtick-wrapped strings get inline code styling
- Everything else renders as readable body text

Shows a "No explanation available" empty state when `explain` was off.

#### `LogPanel.tsx`

A scrolling, terminal-style log panel. Each entry shows:
- **Timestamp** (milliseconds precision)
- **Stage** label (INIT, PARSE, ROUTE, SOLVE, EXPLAIN, DONE, ERROR)
- **Coloured dot** (grey = info, green = success, amber = warning, red = error)
- **Message** text

Includes an **EXPORT JSON** button that downloads all log entries as a structured JSON file. The panel auto-scrolls to the bottom when new entries arrive.

### 6.3 Lib Utilities

#### `lib/api.ts`

Three exported functions:

```typescript
// Send a solve request to the backend and return the result
solveODE(req: SolveRequest): Promise<SolveResult>

// Returns true if the backend is reachable
healthCheck(): Promise<boolean>

// Returns list of available solver names
listSolvers(): Promise<string[]>
```

The backend URL is read from `process.env.NEXT_PUBLIC_BACKEND_URL` (set in `.env.local`), defaulting to `http://localhost:8000`.

#### `lib/examples.ts`

Five pre-built examples with complete `SolveRequest` configurations:

| ID | Label | Category | Equation |
|---|---|---|---|
| `harmonic` | Harmonic Oscillator | Physics | d²x/dt² + ω²x = 0 |
| `lotka_volterra` | Lotka-Volterra | Biology | Predator-prey system |
| `rc_circuit` | RC Circuit | Electronics | dV/dt = (Vs-V)/(RC) |
| `lorenz` | Lorenz System | Chaos | 3-variable chaotic ODE |
| `nl_spring` | Natural Language | NL Input | Plain English description |

Loading an example populates all fields in `InputPanel` instantly.

### 6.4 Types

All shared TypeScript interfaces live in `src/types/index.ts`.

#### `SolveRequest` — sent to the backend

```typescript
interface SolveRequest {
  equation: string;                           // equation string or NL description
  input_mode: "equation" | "natural_language";
  method: "auto" | "euler" | "runge_kutta" | "laplace" | "symbolic" | "numerical";
  t_start: number;
  t_end: number;
  dt: number;
  initial_conditions: Record<string, number>; // e.g. { y: 1.0 }
  parameters: Record<string, number>;         // e.g. { k: 0.5 }
  explain: boolean;
}
```

#### `SolveResult` — returned by the backend

```typescript
interface SolveResult {
  success: boolean;
  method_used: string;
  solver_type: "numerical" | "symbolic" | "laplace";
  equation_parsed: string;
  solution_expression?: string;    // e.g. "y(t) = C1*exp(-k*t)"
  t: number[];                     // time array
  y: number[][];                   // y[variable_index][time_index]
  variable_names: string[];
  execution_time_ms: number;
  explanation?: string;
  convergence_info?: { converged: boolean; iterations: number; residual: number; };
  error?: string;
  warnings?: string[];
}
```

#### `AppStatus` — UI pipeline stage

```typescript
type AppStatus = "idle" | "parsing" | "routing" | "solving" | "explaining" | "done" | "error";
```

---

## 7. API Contract

### `POST /solve`

**Request body:**
```json
{
  "equation": "dy/dt = -k*y",
  "input_mode": "equation",
  "method": "auto",
  "t_start": 0,
  "t_end": 10,
  "dt": 0.05,
  "initial_conditions": { "y": 1.0 },
  "parameters": { "k": 0.5 },
  "explain": true
}
```

**Success response:**
```json
{
  "success": true,
  "method_used": "numerical",
  "solver_type": "numerical",
  "equation_parsed": "dy/dt = -k*y",
  "solution_expression": null,
  "t": [0.0, 0.05, 0.1],
  "y": [[1.0, 0.9753, 0.9512]],
  "variable_names": ["y"],
  "execution_time_ms": 8.3,
  "explanation": "## Equation Analysis\n\nThis is a first-order...",
  "convergence_info": null,
  "warnings": []
}
```

**Error response:**
```json
{
  "success": false,
  "error": "Division by zero in solver: check your dt value",
  "execution_time_ms": 1.2,
  "warnings": []
}
```

### `GET /health`

```json
{
  "status": "ok",
  "autosim": true,
  "llm": true,
  "version": "2.0.0"
}
```

### `GET /solvers`

```json
{
  "solvers": ["auto", "euler", "runge_kutta", "numerical", "symbolic", "laplace"]
}
```

---

## 8. Data Flow — End to End

```
User types equation in InputPanel
         │
         ▼
[InputPanel] validates JSON → calls onSubmit(req)
         │
         ▼
[page.tsx: handleSolve()]
  1. Resets AppState, status → "parsing"
  2. Adds log entry: equation info
  3. status → "routing", logs method info
  4. status → "solving", calls solveODE(req)
         │
         │  fetch POST http://localhost:8000/solve
         ▼
[backend_api.py]
  1. If NL mode → NLPDEParser.parse() via Ollama
  2. parse_ode(equation_str) → parsed AST
  3. If auto → route_solver(parsed) → method name
  4. Dispatch to correct solver module
  5. Solver runs, returns (t, y) or dict
  6. Normalize output shape
  7. If explain → EnhancedSolver.explain() via Ollama
  8. Return SolveResponse JSON
         │
         ▼
[page.tsx: handleSolve() continued]
  5. status → "explaining" (if explanation present)
  6. status → "done", saves result to AppState
  7. activeTab → "plot"
         │
         ▼
[ResultsPanel] re-renders with result
  ├── [PlotPanel]         plots t vs y using Plotly
  ├── [SolutionPanel]     shows metrics and final values
  ├── [ExplanationPanel]  renders LLM explanation text
  └── [LogPanel]          shows all log entries
```

---

## 9. Installation & Setup

### Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | ≥ 3.10 | `python --version` |
| Node.js | ≥ 18 | `node --version` |
| npm | ≥ 9 | `npm --version` |
| Ollama | Latest | `ollama --version` |

### Step 1 — Locate your AutoSim-2 project

```bash
ls AutoSim-2/
# Should show: core/ solvers/ llm_integration/ utils/ app.py main.py
```

### Step 2 — Install Python backend dependencies

```bash
cd AutoSim-2
pip install fastapi uvicorn pydantic

# Should already be present in your environment:
pip install numpy scipy sympy
```

### Step 3 — Place the FastAPI bridge

```bash
# Copy backend_api.py from the frontend folder into AutoSim-2 root:
cp autosim-frontend/backend_api.py AutoSim-2/backend_api.py
```

### Step 4 — Install Node.js frontend dependencies

```bash
cd autosim-frontend
npm install
```

### Step 5 — Pull the Ollama model (for LLM features)

```bash
ollama pull llama3

# Optional: code-focused model for better NL equation parsing
ollama pull deepseek-coder:6.7b
```

If you skip this step, the backend runs in demo mode — explanations will be placeholder text but everything else still works.

---

## 10. Running the Project

You need **three terminals** for the full stack:

### Terminal 1 — Ollama (LLM features)

```bash
ollama serve
# Starts on http://localhost:11434
```

### Terminal 2 — Python Backend

```bash
cd AutoSim-2
python backend_api.py
# Starts FastAPI on http://localhost:8000
```

Verify it works:

```bash
curl http://localhost:8000/health
# → {"status":"ok","autosim":true,"llm":true,"version":"2.0.0"}
```

### Terminal 3 — Next.js Frontend

```bash
cd autosim-frontend
npm run dev
# Starts on http://localhost:3000
```

Open **http://localhost:3000** in your browser.

---

## 11. Environment Variables

### `autosim-frontend/.env.local`

```env
# URL of the FastAPI backend
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Change this to your server's address when deploying. The `NEXT_PUBLIC_` prefix makes the variable accessible in browser-side code.

### Backend — optional Ollama URL override

Add to the top of `backend_api.py` if your Ollama runs on a different port:

```python
OLLAMA_BASE_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
```

---

## 12. Features

### Input
- Equation mode — standard ODE notation with common math operators
- Natural language mode — describe the problem in plain English; Ollama converts it to an equation
- 6 solver methods — Auto, Euler, Runge-Kutta 4, Numerical (SciPy), Symbolic (SymPy), Laplace
- Configurable time range — T₀, T₁, and step size Δt
- JSON initial conditions — any number of variables with initial values
- JSON parameters — named parameters referenced in the equation
- 5 example presets — load complete configurations with one click
- LLM explanation toggle — opt in/out of Ollama explanation generation

### Visualisation
- Time series — all variables plotted with distinct colours, per-variable toggle buttons
- Phase portrait — for systems with 2+ variables; includes start/end markers
- Heatmap — 2D colour view of variable values over time
- Dark scientific theme — transparent backgrounds, custom gridlines, matching the design system

### Results
- Closed-form expression — displayed for symbolic and Laplace solutions
- Metrics dashboard — solve time, step count, time span, variable count
- Final values table — initial, final, and max absolute value per variable
- Convergence info — converged status, iteration count, residual value
- Warnings — non-fatal solver issues highlighted in amber

### LLM Explanation
- Section headers with cyan styling
- Inline code rendering for variable names and expressions
- Math line formatting for equations
- Source attribution showing model and module name

### Logging
- Timestamped entries for every pipeline stage
- Colour-coded levels — info, success, warning, error
- Auto-scroll to latest entry
- JSON export of the complete log

### UI
- Live backend health indicator — polls every 15 seconds
- Pipeline stage tracker — shows which of 5 stages is active
- Skeleton loading states — shimmer animations during computation
- Responsive layout — collapsible sidebar on smaller screens

---

## 13. Supported Equation Types & Examples

### First-order ODE

```
dy/dt = -k*y
Initial conditions: {"y": 1.0}
Parameters: {"k": 0.5}
```

```
dy/dt = r*y*(1 - y/K)
Parameters: {"r": 0.5, "K": 100}
```

### Second-order ODE

```
d2x/dt2 + omega^2*x = 0
Initial conditions: {"x": 1.0, "dx/dt": 0.0}
Parameters: {"omega": 2.0}
```

```
d2x/dt2 + 2*zeta*omega*dx/dt + omega^2*x = 0
Parameters: {"zeta": 0.1, "omega": 3.0}
```

### Coupled systems

```
dx/dt = alpha*x - beta*x*y; dy/dt = delta*x*y - gamma*y
Initial conditions: {"x": 10.0, "y": 5.0}
Parameters: {"alpha": 1.0, "beta": 0.1, "delta": 0.075, "gamma": 1.5}
```

```
dx/dt = sigma*(y-x); dy/dt = x*(rho-z)-y; dz/dt = x*y - beta*z
Initial conditions: {"x": 1.0, "y": 1.0, "z": 1.0}
Parameters: {"sigma": 10.0, "rho": 28.0, "beta": 2.667}
```

### Natural language input

```
"A spring with mass 2 kg and spring constant 8 N/m starting at 3 metres displacement with zero velocity"

"A population growing at 10% per year, starting at 1000, with carrying capacity 50000"

"An RC circuit with resistance 1000 ohms and capacitance 1 millifarad, charging from 0 to 5 volts"
```

---

## 14. Solver Selection Logic

When method is set to `auto`, the router (`core/router.py`) applies these rules in order:

```
1. Is it a linear ODE with constant coefficients?
   └─ Yes → try symbolic (exact solution)
      └─ If SymPy succeeds → return symbolic result
      └─ If SymPy fails   → fall through to numerical

2. Does the equation contain only polynomial nonlinearity?
   └─ Yes → runge_kutta (RK4, reliable for most physics)

3. Is the equation stiff? (large ratio of fastest to slowest timescale)
   └─ Yes → numerical with SciPy LSODA (auto-stiff detection)

4. Is it first-order and simple?
   └─ Yes → euler (fastest, acceptable for exploration)

5. Default → runge_kutta
```

You can always override this by selecting a specific method in the UI.

---

## 15. Adding a New Solver

**Step 1 — Create the solver file in `AutoSim-2/solvers/`:**

```python
# solvers/my_solver.py
import numpy as np

def solve_my_solver(parsed_eq, t_array, initial_conditions, parameters):
    """
    My custom solver.
    Returns: dict with keys 't', 'y', 'variables'
    """
    y_result = ...  # shape: (n_variables, n_time_steps)

    return {
        "t": t_array,
        "y": y_result,
        "variables": list(initial_conditions.keys()),
    }
```

**Step 2 — Register it in `backend_api.py`:**

```python
from solvers.my_solver import solve_my_solver

# In the solver_map dict inside the /solve endpoint:
solver_map = {
    ...
    "my_solver": (solve_my_solver, "numerical"),
}
```

**Step 3 — Add it to the router (optional):**

```python
# In core/router.py, add a condition:
if some_condition(parsed_eq):
    return "my_solver"
```

**Step 4 — Add it to the frontend method list in `InputPanel.tsx`:**

```typescript
const METHODS = [
  ...
  { value: "my_solver", label: "My Solver", desc: "Description of when to use it" },
];
```

**Step 5 — Add it to the TypeScript type in `types/index.ts`:**

```typescript
export type SolverMethod =
  | "auto" | "euler" | "runge_kutta" | "laplace" | "symbolic" | "numerical"
  | "my_solver";
```

---

## 16. Adding a New PDE / Equation Type

To support a new class of equations (e.g. 2D PDEs or delay differential equations):

1. Add a parser rule in `core/parser.py` to recognise the new syntax
2. Add a solver in `solvers/` that handles the spatial grid dimensions
3. Update the output normalisation in `backend_api.py` if the output shape is different (e.g. `[batch, T, Nx, Ny]` for 2D PDEs)
4. In `PlotPanel.tsx`, add a new chart type for 2D spatial solutions (e.g. an animated heatmap over time using Plotly's `animation_frame`)

---

## 17. Extending the Frontend

### Adding a new result tab

1. Add the new tab ID to `AppState["activeTab"]` in `types/index.ts`
2. Add the tab button entry to the `TABS` array in `ResultsPanel.tsx`
3. Create a new component file in `src/components/`
4. Render it inside the content switch block in `ResultsPanel.tsx`

### Adding a new example preset

Edit `src/lib/examples.ts` and add an entry to the `EXAMPLES` array:

```typescript
{
  id: "my_example",
  label: "My Example",
  category: "Physics",
  description: "Brief description shown in the dropdown",
  request: {
    equation: "...",
    input_mode: "equation",
    method: "auto",
    t_start: 0,
    t_end: 10,
    dt: 0.05,
    initial_conditions: { x: 1.0 },
    parameters: { k: 0.5 },
    explain: true,
  },
}
```

### Changing the colour theme

All design tokens are defined in `tailwind.config.ts`:

```typescript
colors: {
  bg:      "#0a0e17",   // page background
  surface: "#0f1624",   // panels
  panel:   "#141d2e",   // inner surfaces
  border:  "#1e2d47",   // dividers
  accent:  "#00d4ff",   // cyan highlight
  green:   "#00ff9d",   // success / done
  amber:   "#ffb800",   // warnings
  red:     "#ff4466",   // errors
  muted:   "#4a5d7a",   // secondary text
  text:    "#c8d8f0",   // primary text
}
```

---

## 18. Connecting to a Different LLM

The LLM modules in `llm_integration/` use Ollama's HTTP API by default. To switch to a different provider:

### OpenAI

```python
import openai
client = openai.OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}]
)
text = response.choices[0].message.content
```

### Anthropic Claude

```python
import anthropic
client = anthropic.Anthropic(api_key="...")
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
)
text = response.content[0].text
```

### Different Ollama model

In your LLM integration files, change the `model` field in the Ollama request:

```python
payload = {
    "model": "llama3",    # change to "mistral", "gemma2", "phi3", etc.
    "stream": False,
    "messages": [...]
}
```

---

## 19. Common Issues & Fixes

### "Backend OFFLINE" badge shows red

The frontend cannot reach `http://localhost:8000`.

```bash
# Check if the backend is running:
curl http://localhost:8000/health

# If not, start it:
cd AutoSim-2 && python backend_api.py
```

Also check that `NEXT_PUBLIC_BACKEND_URL` in `.env.local` matches the actual port.

### "Running in DEMO mode" message in backend terminal

The backend could not import your AutoSim modules. Check that `backend_api.py` is in the same directory as `core/` and `solvers/`.

```python
# In backend_api.py, this line sets the import path:
AUTOSIM_ROOT = os.path.dirname(os.path.abspath(__file__))
# It must equal the directory containing your core/ and solvers/ folders
```

### Import error on `from core.parser import parse_ode`

Your module may use a different function name. Update the import in `backend_api.py`:

```python
# Before:
from core.parser import parse_ode

# After (use your parser's actual function name):
from core.parser import ODEParser
# Then update the call: ODEParser().parse(equation_str)
```

### Solver output format not recognised

If you see `Unknown solver output type`, add a case to the normalisation block in `backend_api.py`:

```python
elif isinstance(raw, np.ndarray):
    t_list = t_arr.tolist()
    y_list = [raw.tolist()]
    var_names = ["y"]
```

### Plotly chart not rendering

`react-plotly.js` is dynamically imported to avoid SSR issues. If the chart area is blank, check the browser console for errors. Confirm the `"use client"` directive is at the top of `PlotPanel.tsx`.

### JSON parse error in initial conditions

The IC and parameter fields expect strict JSON — use double quotes for keys:

```json
// Wrong
{y: 1.0}

// Correct
{"y": 1.0}
```

---

## 20. npm Command Reference

```bash
# Start development server with hot reload
npm run dev

# Type-check and build for production
npm run build

# Start production server (run build first)
npm run start

# Run ESLint
npm run lint

# Install all dependencies fresh
npm install

# Update all dependencies
npm update
```

---

## Quick Start Summary

```bash
# 1. Start Ollama
ollama serve &

# 2. Pull a model
ollama pull llama3

# 3. Start the Python backend
cd AutoSim-2
python backend_api.py &

# 4. Start the frontend
cd autosim-frontend
npm install && npm run dev

# 5. Open browser
open http://localhost:3000
```

---

*AutoSim v2.0 · Python backend by AutoSim-2 · Next.js 14 frontend · LLM via Ollama*