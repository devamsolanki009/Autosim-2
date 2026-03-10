#!/usr/bin/env python3
"""
CAPSTONE PROJECT QUICK START
Demonstration script for LLM-enhanced ODE/PDE solver

This script tests all major features:
1. DeepSeek connection
2. Natural language parsing
3. ODE solving with LLM explanations
4. PDE code generation
5. Enhanced visualizations
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    CAPSTONE PROJECT DEMONSTRATION                         ║
║              LLM-Enhanced ODE/PDE Solver System                          ║
╚═══════════════════════════════════════════════════════════════════════════╝
""")

# Check imports
print("📦 Checking dependencies...")
try:
    import numpy
    print("   ✓ NumPy")
except ImportError:
    print("   ✗ NumPy missing: pip install numpy")
    sys.exit(1)

try:
    import scipy
    print("   ✓ SciPy")
except ImportError:
    print("   ✗ SciPy missing: pip install scipy")
    sys.exit(1)

try:
    import sympy
    print("   ✓ SymPy")
except ImportError:
    print("   ✗ SymPy missing: pip install sympy")
    sys.exit(1)

try:
    import matplotlib
    print("   ✓ Matplotlib")
except ImportError:
    print("   ✗ Matplotlib missing: pip install matplotlib")
    sys.exit(1)

print()

# Import our modules
print("📦 Loading project modules...")
try:
    from llm_integration.deepseek_interface import DeepSeekInterface
    from llm_integration.enhanced_solver import LLMEnhancedSolver
    print("   ✓ LLM integration modules")
except Exception as e:
    print(f"   ✗ Failed to load modules: {e}")
    sys.exit(1)

print()

# Check DeepSeek connection
print("🔗 Checking DeepSeek connection...")
deepseek = DeepSeekInterface()
if deepseek.check_connection():
    print("   ✅ DeepSeek-Coder 6.7B: CONNECTED")
    print("   ✅ Ollama server: RUNNING")
    print()
    llm_available = True
else:
    print("   ⚠️  DeepSeek: NOT CONNECTED")
    print()
    print("   To enable LLM features:")
    print("   1. Install Ollama: https://ollama.com")
    print("   2. Pull model: ollama pull deepseek-coder:6.7b")
    print("   3. Start server: ollama serve")
    print()
    print("   Continuing with limited functionality...")
    print()
    llm_available = False

# Initialize solver
print("🚀 Initializing enhanced solver...")
solver = LLMEnhancedSolver(use_llm=llm_available)
print("   ✓ Solver initialized")
print()

# Test menu
print("═" * 75)
print("SELECT DEMONSTRATION MODE")
print("═" * 75)
print()
print("1. 🎯 Natural Language ODE (requires LLM)")
print("2. 📝 Equation with Enhanced Explanation (requires LLM)")
print("3. 🔬 PDE Code Generation (requires LLM)")
print("4. ⚡ Quick Demo (basic ODE, no LLM)")
print("5. 📊 Full Capstone Demo (all features)")
print()

choice = input("Enter choice (1-5): ").strip()

print()
print("═" * 75)
print()

if choice == '1':
    # Natural language ODE
    if not llm_available:
        print("❌ This feature requires DeepSeek connection")
        sys.exit(1)
    
    print("🎯 NATURAL LANGUAGE ODE DEMONSTRATION")
    print()
    
    description = input("Enter natural language description (or press Enter for default): ").strip()
    if not description:
        description = "Model a damped harmonic oscillator with critical damping"
    
    print(f"\nSolving: \"{description}\"")
    print()
    
    solution = solver.solve_from_natural_language(
        description=description,
        initial_conditions={'x': 1, 'dx': 0},
        time_span=(0, 20)
    )
    
    print()
    print("📊 RESULTS:")
    print(f"   Processing mode: {solution.processing_mode}")
    print(f"   Used LLM: {solution.used_llm}")
    
    if solution.ode_solution:
        print(f"   Equation: {solution.ode_solution.equation}")
        print(f"   Method: {solution.ode_solution.routing_decision.method}")
        print()
        print("🔍 LLM Explanation (first 500 chars):")
        print("   " + "-" * 71)
        for line in solution.natural_language_explanation[:500].split('\n'):
            print(f"   {line}")
        print("   ...")

elif choice == '2':
    # Enhanced explanation
    if not llm_available:
        print("❌ This feature requires DeepSeek connection")
        sys.exit(1)
    
    print("📝 EQUATION WITH ENHANCED EXPLANATION")
    print()
    
    equation = input("Enter equation (or press Enter for default): ").strip()
    if not equation:
        equation = "x'' + 0.2*x' + x + 0.1*x**3 = cos(t)"
    
    print(f"\nSolving: {equation}")
    print()
    
    solution = solver.solve_with_explanation(
        equation=equation,
        initial_conditions={'x': 1, 'dx': 0},
        time_span=(0, 50)
    )
    
    print()
    print("📊 RESULTS:")
    if solution.ode_solution:
        print(f"   Classification: {solution.ode_solution.classification}")
        print(f"   Method: {solution.ode_solution.routing_decision.method}")
        print()
        print("🔍 LLM Explanation:")
        print("   " + "-" * 71)
        for line in solution.natural_language_explanation.split('\n')[:20]:
            print(f"   {line}")

elif choice == '3':
    # PDE code generation
    if not llm_available:
        print("❌ This feature requires DeepSeek connection")
        sys.exit(1)
    
    print("🔬 PDE CODE GENERATION (CodePDE-inspired)")
    print()
    
    description = input("Enter PDE description (or press Enter for default): ").strip()
    if not description:
        description = "Solve the 1D heat equation with Dirichlet boundary conditions"
    
    print(f"\nGenerating solver for: \"{description}\"")
    print()
    
    solution = solver.solve_from_natural_language(description=description)
    
    print()
    print("📊 RESULTS:")
    if solution.pde_spec:
        print(f"   PDE Type: {solution.pde_spec.equation_type}")
        print(f"   Equation: {solution.pde_spec.equation}")
        print(f"   Domain: {solution.pde_spec.domain}")
        print()
        
        if solution.generated_solver_code:
            lines = solution.generated_solver_code.split('\n')
            print(f"✓ Generated {len(lines)} lines of code")
            print()
            print("Generated Code (first 30 lines):")
            print("   " + "-" * 71)
            for i, line in enumerate(lines[:30], 1):
                print(f"   {i:3d} | {line}")
            if len(lines) > 30:
                print(f"   ... ({len(lines) - 30} more lines)")

elif choice == '4':
    # Quick demo - no LLM needed
    print("⚡ QUICK DEMO (Basic ODE Solving)")
    print()
    
    from main import ODESolverSystem
    basic_solver = ODESolverSystem()
    
    equation = "x'' + 2*x' + x = 0"
    print(f"Solving: {equation}")
    print("Initial conditions: x(0)=1, x'(0)=0")
    print()
    
    solution = basic_solver.solve(
        equation=equation,
        initial_conditions={'x': 1, 'dx': 0},
        time_span=(0, 20),
        save_plot=False
    )
    
    print()
    print("📊 RESULTS:")
    print(f"   Classification: {solution.classification}")
    print(f"   Solver: {solution.routing_decision.solver_type} ({solution.routing_decision.method})")
    
    if solution.numerical_solution:
        stats = solution.numerical_solution.statistics
        print()
        print("   Statistics:")
        print(f"      Final value: {stats['x_final']:.6f}")
        print(f"      Maximum: {stats['x_max']:.6f}")
        print(f"      Minimum: {stats['x_min']:.6f}")

elif choice == '5':
    # Full demo
    print("📊 FULL CAPSTONE DEMONSTRATION")
    print()
    
    if not llm_available:
        print("⚠️  LLM not available - showing basic features only")
        print()
    
    # Demo 1: Basic ODE
    print("="*75)
    print("DEMO 1: Traditional ODE Solving")
    print("="*75)
    print()
    
    from main import ODESolverSystem
    basic_solver = ODESolverSystem()
    
    eq1 = "x'' + x = 0"
    print(f"Equation: {eq1}")
    sol1 = basic_solver.solve(eq1, {'x': 1, 'dx': 0}, (0, 20), save_plot=False)
    print(f"✓ Solved using {sol1.routing_decision.method}")
    print(f"  Classification: {sol1.classification['family']}")
    print()
    
    # Demo 2: Natural language (if LLM available)
    if llm_available:
        print("="*75)
        print("DEMO 2: Natural Language Input (LLM Feature)")
        print("="*75)
        print()
        
        nl_input = "Model a spring-mass-damper system"
        print(f"Input: \"{nl_input}\"")
        sol2 = solver.solve_from_natural_language(nl_input, {'x': 1, 'dx': 0}, (0, 20))
        print(f"✓ Extracted equation: {sol2.ode_solution.equation if sol2.ode_solution else 'N/A'}")
        print(f"  Used LLM: {sol2.used_llm}")
        print()
        
        # Demo 3: PDE generation
        print("="*75)
        print("DEMO 3: PDE Solver Generation (CodePDE-inspired)")
        print("="*75)
        print()
        
        pde_input = "Solve the 1D heat equation"
        print(f"Input: \"{pde_input}\"")
        sol3 = solver.solve_from_natural_language(pde_input)
        if sol3.pde_spec:
            print(f"✓ Identified: {sol3.pde_spec.equation_type} equation")
            print(f"  Domain: {sol3.pde_spec.domain}")
            if sol3.generated_solver_code:
                print(f"  Generated code: {len(sol3.generated_solver_code.split(chr(10)))} lines")
        print()
    
    print("="*75)
    print("DEMONSTRATION COMPLETE")
    print("="*75)

else:
    print("Invalid choice")
    sys.exit(1)

print()
print("═" * 75)
print()
print("✅ CAPSTONE DEMONSTRATION COMPLETE")
print()
print("Next steps:")
print("   • Start UI: python ui/api_server_enhanced.py")
print("   • View docs: cat CAPSTONE_PROJECT_DOCUMENTATION.md")
print("   • Run tests: python -m pytest tests/")
print()
print("═" * 75)