"""
ODE Solver System - Streamlit UI
Production-Grade Interactive Interface
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import sys
import os
from pathlib import Path
from llm_integration.enhanced_solver import LLMEnhancedSolver
# Add the ODE solver to path
sys.path.insert(0, str(Path(__file__).parent))

from main import ODESolverSystem, CompleteSolution

# Page configuration
st.set_page_config(
    page_title="ODE Solver System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
        font-size: 1.1rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 4px solid #1f77b4;
    }
    .metric-card h3 {
        margin: 0;
        color: #333;
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card .value {
        font-size: 1.8rem;
        color: #1f77b4;
        font-weight: bold;
        margin-top: 0.5rem;
    }
    .info-box {
        background-color: #f0f7ff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #f0fdf4;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #22c55e;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fffbeb;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'solution' not in st.session_state:
        st.session_state.solution = None

    if 'solver_basic' not in st.session_state:
        st.session_state.solver_basic = ODESolverSystem()

    if 'solver_llm' not in st.session_state:
        st.session_state.solver_llm = LLMEnhancedSolver(use_llm=True)

    if 'solving' not in st.session_state:
        st.session_state.solving = False

def render_header():
    """Render the application header"""
    st.markdown('<h1 class="main-header">ODE Solver System</h1>', unsafe_allow_html=True)
    st.markdown("""
        <div class='sub-header'>
            Production-Grade Differential Equation Solver<br>
            <strong>Zero Hallucination Architecture</strong> • All computations by SymPy & SciPy
        </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with input controls"""
    with st.sidebar:
        st.header(" Configuration")
        
        # Equation input
        st.subheader("1️. Equation")
        
        # Initialize example equation in session state if needed
        if 'current_equation' not in st.session_state:
            st.session_state.current_equation = "x'' + 0.2*x' + x + 0.1*x**3 = cos(t)"
        
        equation = st.text_area(
            "Enter ODE (use x as dependent variable, t as independent)",
            value=st.session_state.current_equation,
            height=100,
            help="Supported: x'', x', dx/dt, d²x/dt², sin(t), cos(t), exp(t), x**2, etc.",
            key="equation_input"
        )
        
        # Example equations
        with st.expander("Example Equations", expanded=False):
            examples = {
                "Simple Harmonic": "x'' + x = 0",
                "Damped Oscillator": "x'' + 2*x' + x = 0",
                "Forced Duffing": "x'' + 0.2*x' + x + 0.1*x**3 = cos(t)",
                "Van der Pol": "x'' - (1 - x**2)*x' + x = 0",
                "Stiff System": "x'' + 1000*x' + x = 0",
                "Underdamped": "x'' + 0.5*x' + 4*x = 0",
                "Overdamped": "x'' + 5*x' + 4*x = 0",
                "Forced Harmonic": "x'' + 0.1*x' + x = sin(2*t)",
            }
            
            cols = st.columns(2)
            for idx, (name, eq) in enumerate(examples.items()):
                col = cols[idx % 2]
                with col:
                    if st.button(name, key=f"example_{name}", use_container_width=True):
                        st.session_state.current_equation = eq
                        st.rerun()
        
        st.divider()
        
        # Initial conditions
        st.subheader("2️. Initial Conditions")
        col1, col2 = st.columns(2)
        with col1:
            x0 = st.number_input("x(0)", value=1.0, step=0.1, format="%.2f")
        with col2:
            dx0 = st.number_input("x'(0)", value=0.0, step=0.1, format="%.2f")
        
        st.divider()
        
        # Time span
        st.subheader("3️. Time Range")
        col1, col2 = st.columns(2)
        with col1:
            t_start = st.number_input("Start", value=0.0, step=1.0, format="%.1f")
        with col2:
            t_end = st.number_input("End", value=50.0, step=5.0, format="%.1f")
        
        st.divider()
        
        # Advanced options
        with st.expander("Advanced Options"):
            hint = st.selectbox(
                "Routing Hint",
                ["None", "stiff", "fast_oscillation", "slow_decay"],
                help="Give the router a hint about the system behavior"
            )
            hint = None if hint == "None" else hint
        
        st.divider()
        #  LLM Toggle (ADD THIS BLOCK HERE)
        use_llm = st.checkbox(
            "Enable LLM Insights",
            value=True,
            help="Enable AI-powered interpretation and explanation layer"
        )
        # Solve button
        solve_button = st.button(
            "Solve ODE", 
            type="primary", 
            use_container_width=True,
            disabled=st.session_state.solving
        )
        
        # Info about zero hallucination
        st.divider()
        st.markdown("""
        <div style='background: #f0f7ff; padding: 1rem; border-radius: 0.5rem; font-size: 0.85rem;'>
            <strong> Zero Hallucination Guarantee</strong><br>
            All mathematical computations performed by:<br>
            • SymPy (symbolic)<br>
            • SciPy (numerical)<br>
            • NumPy (arrays)<br>
            <em>No LLM computation involved!</em>
        </div>
        """, unsafe_allow_html=True)
        
        return {
            'equation': equation,
            'initial_conditions': {'x': x0, 'dx': dx0},
            'time_span': (t_start, t_end),
            'hint': hint,
            'use_llm': use_llm,
            'solve': solve_button
        }

def render_classification(solution: CompleteSolution):
    """Render the ODE classification section"""
    st.markdown("### 1. Classification")
    
    classification = solution.classification
    
    cols = st.columns(4)
    
    metrics = [
        ("Order", f"{classification['order']}", "📊"),
        ("Type", "Linear" if classification['linear'] else "Nonlinear", "🔢"),
        ("Family", classification['family'], "🏷️"),
        ("Stiff", "Yes" if classification['stiff'] else "No", "⚡")
    ]
    
    for col, (label, value, icon) in zip(cols, metrics):
        with col:
            st.markdown(f"""
                <div class='metric-card'>
                    <h3>{icon} {label}</h3>
                    <div class='value'>{value}</div>
                </div>
            """, unsafe_allow_html=True)

def render_routing_decision(solution: CompleteSolution):
    """Render the solver decision section"""
    st.markdown("### 2️. Solver Decision")
    
    decision = solution.routing_decision
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div class='info-box'>
                <strong>Approach:</strong> {decision.solver_type.upper()}<br>
                <strong>Method:</strong> {decision.method}
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class='success-box'>
                <strong>Reason:</strong><br>{decision.reason}
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        stiff_indicator = "🔴" if decision.stiffness_detected else "🟢"
        st.markdown(f"""
            <div class='info-box'>
                <strong>Stiffness:</strong> {stiff_indicator}<br>
                <strong>Family:</strong> {decision.equation_family}
            </div>
        """, unsafe_allow_html=True)

def render_symbolic_solution(solution: CompleteSolution):
    """Render symbolic solution if available"""
    if solution.symbolic_solution is None:
        return
    
    st.markdown("### 3️. Symbolic Solution")
    
    sym_sol = solution.symbolic_solution
    
    # Display solution type
    st.info(f"**Solution Type:** {sym_sol.solution_type}")
    
    # Show characteristic roots if available
    if sym_sol.characteristic_roots:
        st.markdown("**Characteristic Roots:**")
        roots_str = ", ".join([str(r) for r in sym_sol.characteristic_roots])
        st.code(roots_str, language="python")
    
    # Show derivation steps
    with st.expander(" View Step-by-Step Derivation", expanded=False):
        for step in sym_sol.derivation_steps:
            st.markdown(f"**Step {step.step_number}: {step.description}**")
            st.latex(step.equation)
            st.divider()

def render_numerical_solution(solution: CompleteSolution):
    """Render numerical solution"""
    if solution.numerical_solution is None:
        return
    
    num_sol = solution.numerical_solution
    
    if not num_sol.success:
        st.error(f"Numerical integration failed: {num_sol.message}")
        return
    
    title = "3️.  Numerical Solution" if solution.symbolic_solution is None else "4️⃣ Numerical Solution"
    st.markdown(f"### {title}")
    
    # Statistics
    stats = num_sol.statistics
    
    cols = st.columns(4)
    
    metrics_data = [
        ("Final x", stats['x_final'], "📍"),
        ("Max x", stats['x_max'], "📈"),
        ("Min x", stats['x_min'], "📉"),
        ("Range", stats['x_max'] - stats['x_min'], "📏")
    ]
    
    for col, (label, value, icon) in zip(cols, metrics_data):
        with col:
            st.metric(label, f"{value:.6f}", delta=icon)
    
    # Additional statistics if available
    if 'period_estimate' in stats:
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Estimated Period", f"{stats['period_estimate']:.4f}", delta="⏱️")
        with col2:
            st.metric("Estimated Frequency", f"{stats['frequency_estimate']:.4f} Hz", delta="🌊")

def render_visualization(solution: CompleteSolution):
    """Render the solution visualization"""
    st.markdown("### 5️. Visualization")
    
    if solution.visualization is None:
        st.warning("No visualization available")
        return
    
    try:
        # Display Matplotlib figure directly
        st.pyplot(solution.visualization, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error displaying visualization: {e}")


def render_explanation(solution: CompleteSolution):
    """Render the explanation section"""
    st.markdown("### 6️. Interpretation & Summary")
    
    # Display the structured explanation
    st.markdown(f"""
    <div class='info-box'>
        <pre style='white-space: pre-wrap; font-family: monospace; font-size: 0.9rem;'>{solution.explanation}</pre>
    </div>
    """, unsafe_allow_html=True)

def render_technical_details(solution: CompleteSolution):
    """Render technical details tab"""
    st.markdown("###  Technical Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Equation Information")
        st.json({
            "Original Equation": solution.equation,
            "Order": solution.classification['order'],
            "Linear": solution.classification['linear'],
            "Homogeneous": solution.classification['homogeneous'],
            "Family": solution.classification['family']
        })
    
    with col2:
        st.markdown("#### Solver Information")
        st.json({
            "Solver Type": solution.routing_decision.solver_type,
            "Method": solution.routing_decision.method,
            "Stiffness Detected": solution.routing_decision.stiffness_detected,
            "Reason": solution.routing_decision.reason
        })
    
    if solution.numerical_solution and solution.numerical_solution.success:
        st.markdown("#### Numerical Solution Details")
        num_sol = solution.numerical_solution
        st.json({
            "Method": num_sol.method,
            "Time Points": len(num_sol.t),
            "Time Range": f"[{num_sol.t[0]}, {num_sol.t[-1]}]",
            "State Dimensions": num_sol.y.shape[0],
            "Success": num_sol.success,
            "Message": num_sol.message
        })
        
        # Raw data preview
        with st.expander("View Raw Data (First 10 points)"):
            import pandas as pd
            df_data = {
                't': num_sol.t[:10],
                'x': num_sol.y[0][:10]
            }
            if num_sol.y.shape[0] > 1:
                df_data['dx/dt'] = num_sol.y[1][:10]
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)

def render_about():
    """Render about/help information"""
    st.markdown("### About This System")
    
    st.markdown("""
    ##  Zero Hallucination ODE Solver
    
    This is a **production-grade ODE solver** with a **zero hallucination architecture** that ensures
    all mathematical computations are performed by verified libraries, not AI models.
    
    ### Key Features
    
    -  **Automatic Equation Parsing** - Handles multiple notations (x'', dx/dt, d²x/dt²)
    -  **Intelligent Routing** - Deterministic solver selection based on equation properties
    -  **Symbolic Solutions** - Step-by-step derivations using SymPy
    -  **Numerical Integration** - SciPy's industrial-strength ODE solvers
    -  **Stiffness Detection** - Automatic detection and appropriate method selection
    -  **Professional Visualization** - Multi-panel plots with phase portraits
    
    ###  Architecture Principle
    
    **No LLM Computation** - The architectural constraint ensures safety:
    
    ```
    User Input
        ↓
    Parser (Regex, deterministic)
        ↓
    Router (Rule-based logic)
        ↓
    Solver (SymPy / SciPy)
        ↓
    Visualization (Matplotlib)
        ↓
    Explanation (LLM - interpretation only)
    ```
    
    ###  Supported ODE Types
    
    | Type | Order | Solver | Methods |
    |------|-------|--------|---------|
    | Linear Constant Coefficient | 1st, 2nd | Symbolic | SymPy |
    | Nonlinear | Any | Numerical | RK45, RK23 |
    | Stiff Systems | Any | Numerical | Radau, BDF |
    | General | Any | Numerical | LSODA |
    
    ###  Equation Families Recognized
    
    - Simple Harmonic Oscillator
    - Damped Harmonic Oscillator  
    - Forced Harmonic Oscillator
    - Duffing Oscillator (nonlinear)
    - Van der Pol Oscillator
    - Pendulum Equations
    - General Linear/Nonlinear
    
    ###  Zero Hallucination Guarantee
    
    Every numerical value in the output is computed by:
    
    - **SymPy** - Symbolic mathematics (peer-reviewed)
    - **SciPy** - Numerical integration (industry standard)
    - **NumPy** - Array operations (verified)
    - **Matplotlib** - Visualization (trusted)
    
    The LLM is **only** used for:
    - Generating human-readable explanations
    - Providing physical interpretation
    - Contextualizing results
    
    It **never** performs mathematical computation.
    
    ###  Usage Tips
    
    1. **Equation Notation**: Use `x` for the dependent variable and `t` for time
    2. **Derivatives**: Write as `x''`, `x'` or use `dx/dt` notation
    3. **Functions**: Use standard Python math: `sin(t)`, `cos(t)`, `exp(t)`
    4. **Nonlinear Terms**: Use `**` for powers: `x**2`, `x**3`
    5. **Initial Conditions**: Specify both x(0) and x'(0) for second-order ODEs
    
    ###  Examples to Try
    
    **Beginner:**
    - `x'' + x = 0` (simple harmonic)
    - `x'' + 2*x' + x = 0` (damped)
    
    **Intermediate:**
    - `x'' + 0.1*x' + x = cos(t)` (forced)
    - `x'' + 0.5*x' + 4*x = 0` (underdamped)
    
    **Advanced:**
    - `x'' + 0.2*x' + x + 0.1*x**3 = cos(t)` (Duffing)
    - `x'' - (1 - x**2)*x' + x = 0` (Van der Pol)
    - `x'' + 1000*x' + x = 0` (stiff system)
    
    ###  Performance Characteristics
    
    - **Parsing**: < 10ms
    - **Symbolic Solving**: < 100ms (when applicable)
    - **Numerical Integration**: 100-500ms (1000 points)
    - **Visualization**: 200-400ms
    
    ---
    
    **Built with:**  
    Python • Streamlit • SymPy • SciPy • NumPy • Matplotlib
    
    **Architecture:**  
    Zero Hallucination • Deterministic Routing • Verified Computation
    """)

def main():
    """Main application"""
    initialize_session_state()
    render_header()
    
    # Get input parameters from sidebar
    params = render_sidebar()
    
    # Main content area
    if params['solve']:
        st.session_state.solving = True
        
        try:
            with st.spinner("Solving ODE... This may take a few seconds"):
                # Solve the ODE
                if params['use_llm']:
                    enhanced_solution = st.session_state.solver_llm.solve_with_explanation(
                        equation=params['equation'],
                        initial_conditions=params['initial_conditions'],
                        time_span=params['time_span']
                    )
                    solution = enhanced_solution.ode_solution
                    st.session_state.enhanced_solution = enhanced_solution
                else:
                    solution = st.session_state.solver_basic.solve(
                        equation=params['equation'],
                        initial_conditions=params['initial_conditions'],
                        time_span=params['time_span'],
                        hint=params['hint']
                    )
                st.session_state.solution = solution
            
            st.success(" Solution computed successfully!")
            st.session_state.solving = False
            
        except Exception as e:
            st.error(f"Error: {str(e)}")
            with st.expander("View Error Details"):
                st.exception(e)
            st.session_state.solving = False
            return
    
    # Display solution if available
    if st.session_state.solution is not None:
        solution = st.session_state.solution
        
        # Create tabs for organized display
        tab1, tab2, tab3, tab4 = st.tabs(["Results", "LLM Insights", "Technical Details", "About"])
        
        with tab1:
            st.markdown("## Solution Results")
            st.divider()
            
            render_classification(solution)
            st.divider()
            
            render_routing_decision(solution)
            st.divider()
            
            render_symbolic_solution(solution)
            
            render_numerical_solution(solution)
            st.divider()
            
            render_visualization(solution)
            st.divider()
            
            render_explanation(solution)
        with tab2:
            if params.get('use_llm') and hasattr(st.session_state, 'enhanced_solution'):
                enhanced = st.session_state.enhanced_solution
                
                st.markdown("## LLM Insights")
                st.divider()
                
                st.markdown("### Natural Language Explanation")
                st.write(enhanced.natural_language_explanation)
                
                st.divider()
                st.markdown("### Physical Interpretation")
                st.write(enhanced.physical_interpretation)
                
            else:
                st.info("LLM mode disabled or not available.")
        with tab3:
            render_technical_details(solution)
        
        with tab4:
            render_about()
    
    else:
        # Welcome screen
        st.markdown("""
        <div class='info-box'>
            <h3>Welcome to the ODE Solver System!</h3>
            <p>Get started by entering an ODE equation in the sidebar on the left.</p>
            <p>Try one of the example equations or write your own using standard mathematical notation.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick start guide
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### Supported Notation
            
            **Derivatives:**
            - `x''` or `x'` for derivatives
            - `dx/dt`, `d²x/dt²` also supported
            
            **Functions:**
            - `sin(t)`, `cos(t)`, `exp(t)`
            - `tan(t)`, `log(t)`, `sqrt(t)`
            
            **Operators:**
            - `+`, `-`, `*`, `/` (basic arithmetic)
            - `**` or `^` for powers
            
            **Variables:**
            - Always use `x` (dependent)
            - Always use `t` (independent)
            """)
        
        with col2:
            st.markdown("""
            ### Quick Examples
            
            **Linear Systems:**
            1. `x'' + x = 0` - Simple harmonic
            2. `x'' + 2*x' + x = 0` - Critical damping
            3. `x'' + 0.1*x' + x = sin(t)` - Forced oscillation
            
            **Nonlinear Systems:**
            1. `x'' + x + 0.1*x**3 = 0` - Duffing
            2. `x'' - (1-x**2)*x' + x = 0` - Van der Pol
            3. `x'' + sin(x) = 0` - Pendulum
            
            **Stiff Systems:**
            1. `x'' + 1000*x' + x = 0` - High damping
            """)
        
        st.divider()
        
        # Feature highlights
        st.markdown("###  What Makes This Special?")
        
        cols = st.columns(3)
        
        with cols[0]:
            st.markdown("""
            <div class='success-box'>
                <h4>Zero Hallucination</h4>
                <p>All math done by SymPy & SciPy - no AI computation</p>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown("""
            <div class='info-box'>
                <h4>Smart Routing</h4>
                <p>Automatic solver selection based on equation properties</p>
            </div>
            """, unsafe_allow_html=True)
        
        with cols[2]:
            st.markdown("""
            <div class='warning-box'>
                <h4>Rich Visualization</h4>
                <p>Multi-panel plots with phase portraits</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()