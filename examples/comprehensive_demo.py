"""
Comprehensive Example: Complete ODE Solver System
Demonstrates the exact output format you requested
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import ODESolverSystem


def example_duffing_forced():
    """
    Example matching your specification:
    x'' + 0.2x' + x + 0.1x³ = cos(t)
    x(0)=1, x'(0)=0
    """
    
    print("\n" + "🎯 "*40)
    print("COMPREHENSIVE EXAMPLE: Forced Duffing Oscillator")
    print("🎯 "*40 + "\n")
    
    solver = ODESolverSystem()
    
    equation = "x'' + 0.2*x' + x + 0.1*x**3 = cos(t)"
    initial_conditions = {'x': 1, 'dx': 0}
    time_span = (0, 50)
    
    print("INPUT:")
    print(f"  Equation: {equation}")
    print(f"  Initial conditions: x(0) = {initial_conditions['x']}, x'(0) = {initial_conditions['dx']}")
    print(f"  Time span: {time_span}")
    print("\n" + "="*80 + "\n")
    
    # Solve
    solution = solver.solve(
        equation=equation,
        initial_conditions=initial_conditions,
        time_span=time_span,
        save_plot=True,
        plot_path='/mnt/user-data/outputs/duffing_example.png'
    )
    
    print("\n" + "="*80)
    print("EXPECTED OUTPUT FORMAT")
    print("="*80 + "\n")
    
    # Format output as specified
    print("1. CLASSIFICATION")
    print("-" * 80)
    print(f"   Order: {solution.classification['order']}")
    print(f"   Type: {'Linear' if solution.classification['linear'] else 'Nonlinear'}")
    print(f"   System: {solution.classification['family']}")
    print(f"   Symbolic Solution: {'Yes' if solution.routing_decision.symbolic_feasible else 'No'}")
    print(f"   Stiff: {'Yes' if solution.classification['stiff'] else 'No'}")
    print()
    
    print("2. SOLVER DECISION")
    print("-" * 80)
    print(f"   Solver Type: {solution.routing_decision.solver_type.upper()}")
    print(f"   Method: {solution.routing_decision.method}")
    print(f"   Reason: {solution.routing_decision.reason}")
    print()
    
    print("3. MATHEMATICAL FORMULATION")
    print("-" * 80)
    print("   Converted to first-order system:")
    print("   Let y₁ = x, y₂ = x'")
    print("   Then:")
    print("       dy₁/dt = y₂")
    print("       dy₂/dt = cos(t) - 0.2y₂ - y₁ - 0.1y₁³")
    print()
    
    if solution.numerical_solution and solution.numerical_solution.success:
        stats = solution.numerical_solution.statistics
        
        print("4. NUMERICAL RESULTS")
        print("-" * 80)
        print(f"   Time span: [0, 50]")
        print(f"   Integration points: {len(solution.numerical_solution.t)}")
        print(f"   Method: {solution.numerical_solution.method}")
        print()
        print("   Final state:")
        print(f"       x(50) = {stats['x_final']:.6f}")
        print(f"       x'(50) = {stats.get('v_final', 0):.6f}")
        print()
        print("   Statistics:")
        print(f"       max(x) = {stats['x_max']:.6f}")
        print(f"       min(x) = {stats['x_min']:.6f}")
        print(f"       mean(x) = {stats['x_mean']:.6f}")
        print(f"       std(x) = {stats['x_std']:.6f}")
        
        if 'period_estimate' in stats:
            print(f"       Estimated period: {stats['period_estimate']:.6f}")
            print(f"       Estimated frequency: {stats['frequency_estimate']:.6f} Hz")
        print()
    
    print("5. VISUALIZATION")
    print("-" * 80)
    if solution.visualization_path:
        print(f"   ✓ Plot generated: {solution.visualization_path}")
        print("   Contents:")
        print("       • Position vs Time x(t)")
        print("       • Velocity vs Time x'(t)")
        print("       • Phase portrait (x vs x')")
    print()
    
    print("6. PHYSICAL INTERPRETATION")
    print("-" * 80)
    print("   This is a forced Duffing oscillator, characterized by:")
    print("   • Nonlinear restoring force (cubic term 0.1x³)")
    print("   • Weak damping (coefficient 0.2)")
    print("   • Harmonic forcing (cos(t))")
    print()
    print("   The cubic nonlinearity causes:")
    print("   • Amplitude-dependent frequency")
    print("   • Potential for multiple stable states")
    print("   • Rich dynamical behavior")
    print()
    print("   In this solution:")
    if solution.numerical_solution and solution.numerical_solution.success:
        x_range = stats['x_max'] - stats['x_min']
        print(f"   • Oscillation amplitude: ≈ {x_range/2:.4f}")
        print(f"   • Solution bounded between [{stats['x_min']:.4f}, {stats['x_max']:.4f}]")
        if 'period_estimate' in stats:
            print(f"   • Approximate period: {stats['period_estimate']:.4f} time units")
    print()
    
    print("="*80)
    print("SYSTEM COMPLETE - NO LLM COMPUTATION INVOLVED")
    print("="*80)
    print("\nAll mathematical operations performed by:")
    print("  • SymPy (symbolic algebra)")
    print("  • SciPy (numerical integration)")
    print("  • NumPy (array operations)")
    print("\nLLM role: Classification assistance and explanation ONLY")
    print("\n" + "✅ "*40 + "\n")


def example_harmonic():
    """Simple harmonic oscillator - symbolic solution"""
    
    print("\n" + "🎯 "*40)
    print("EXAMPLE: Simple Harmonic Oscillator (Symbolic)")
    print("🎯 "*40 + "\n")
    
    solver = ODESolverSystem()
    
    equation = "x'' + x = 0"
    initial_conditions = {'x': 1, 'dx': 0}
    
    solution = solver.solve(
        equation=equation,
        initial_conditions=initial_conditions,
        time_span=(0, 20),
        save_plot=True,
        plot_path='/mnt/user-data/outputs/harmonic_example.png'
    )
    
    if solution.symbolic_solution:
        print("\nSYMBOLIC DERIVATION:")
        print("="*80)
        for step in solution.symbolic_solution.derivation_steps:
            print(f"\nStep {step.step_number}: {step.description}")
            print(f"  {step.equation}")
        print()


def example_stiff_system():
    """Stiff system - special handling"""
    
    print("\n" + "🎯 "*40)
    print("EXAMPLE: Stiff System")
    print("🎯 "*40 + "\n")
    
    solver = ODESolverSystem()
    
    # Create a stiff system
    equation = "x'' + 1000*x' + x = 0"
    initial_conditions = {'x': 1, 'dx': 0}
    
    solution = solver.solve(
        equation=equation,
        initial_conditions=initial_conditions,
        time_span=(0, 10),
        hint="stiff system",
        save_plot=True,
        plot_path='/mnt/user-data/outputs/stiff_example.png'
    )
    
    print(f"\n⚠ Stiff system detected: {solution.routing_decision.stiffness_detected}")
    print(f"   Solver used: {solution.routing_decision.method}")


if __name__ == '__main__':
    # Run all examples
    example_duffing_forced()
    example_harmonic()
    example_stiff_system()
    
    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETE")
    print("="*80)
    print("\nGenerated files:")
    print("  • /mnt/user-data/outputs/duffing_example.png")
    print("  • /mnt/user-data/outputs/harmonic_example.png")
    print("  • /mnt/user-data/outputs/stiff_example.png")
    print()