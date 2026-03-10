"""
Complete ODE Solver System
Orchestrates parsing, routing, solving, and explanation
"""

import sys
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.parser import ODEParser, ODEComponents
from core.router import ODERouter, RoutingDecision
from solvers.symbolic import SymbolicSolver, SymbolicSolution
from solvers.numerical import NumericalSolver, NumericalSolution
from utils.visualization import ODEVisualizer


@dataclass
@dataclass
class CompleteSolution:
    equation: str
    classification: Dict
    routing_decision: RoutingDecision
    symbolic_solution: Optional[SymbolicSolution]
    numerical_solution: Optional[NumericalSolution]
    visualization: Optional[object]   # Matplotlib figure
    explanation: str



class ODESolverSystem:
    """
    Complete ODE Solver System
    
    NO LLM COMPUTATION - Only explanation and context
    """
    
    def __init__(self):
        self.parser = ODEParser()
        self.router = ODERouter()
        self.symbolic_solver = SymbolicSolver()
        self.numerical_solver = NumericalSolver()
        self.visualizer = ODEVisualizer()
    
    def solve(self,
          equation: str,
          initial_conditions: Dict[str, float],
          time_span: Tuple[float, float] = (0, 50),
          hint: Optional[str] = None,
          save_plot: bool = False,
          show_plot: bool = False,
          plot_path: Optional[str] = None) -> CompleteSolution:
        """
        Complete ODE solving pipeline
        
        Args:
            equation: ODE string (e.g., "x'' + 2*x' + x = 0")
            initial_conditions: {'x': 1, 'dx': 0}
            time_span: (t_start, t_end) for numerical solutions
            hint: Optional hint for routing (e.g., "stiff")
            save_plot: Whether to save visualization
            plot_path: Custom path for plot
        
        Returns:
            CompleteSolution with all results
        """
        
        print("="*80)
        print("ODE SOLVER SYSTEM - COMPLETE PIPELINE")
        print("="*80)
        print()
        
        # Step 1: Parse equation
        print("Step 1: PARSING EQUATION")
        print("-" * 80)
        components = self.parser.parse(equation, initial_conditions)
        print(f"✓ Equation parsed: {equation}")
        print(f"  Order: {components.order}")
        print(f"  Linear: {components.is_linear}")
        print(f"  Homogeneous: {components.is_homogeneous}")
        print(f"  Coefficients: {components.coefficients}")
        if components.nonlinear_terms:
            print(f"  Nonlinear terms: {components.nonlinear_terms}")
        print()
        
        # Step 2: Route to solver
        print("Step 2: ROUTING DECISION")
        print("-" * 80)
        decision = self.router.route(components, time_span, hint)
        print(f"✓ Solver selected: {decision.solver_type.upper()}")
        print(f"  Method: {decision.method}")
        print(f"  Reason: {decision.reason}")
        print(f"  Equation family: {decision.equation_family}")
        print(f"  Stiffness detected: {decision.stiffness_detected}")
        print()
        
        # Step 3: Solve
        symbolic_sol = None
        numerical_sol = None
        
        if decision.solver_type == 'symbolic':
            print("Step 3: SYMBOLIC SOLUTION")
            print("-" * 80)
            
            try:
                symbolic_sol = self.symbolic_solver.solve(components, initial_conditions)
                
                print("✓ Symbolic solution computed")
                print()
                print("DERIVATION STEPS:")
                for step in symbolic_sol.derivation_steps:
                    print(f"\n  {step.step_number}. {step.description}")
                    print(f"     {step.equation}")
                
                print()
                print(f"Solution type: {symbolic_sol.solution_type}")
                if symbolic_sol.characteristic_roots:
                    print(f"Characteristic roots: {symbolic_sol.characteristic_roots}")
                
                # Also compute numerical for plotting
                print("\n  Computing numerical values for visualization...")
                numerical_sol = self.numerical_solver.solve(
                    components, initial_conditions, time_span, method='RK45'
                )
            
            except Exception as e:
                print(f"✗ Symbolic solution failed: {e}")
                print("  Falling back to numerical method...")
                decision.solver_type = 'numerical'
                decision.method = 'RK45'
        
        if decision.solver_type == 'numerical' or numerical_sol is None:
            print("Step 3: NUMERICAL SOLUTION")
            print("-" * 80)
            
            numerical_sol = self.numerical_solver.solve(
                components, 
                initial_conditions, 
                time_span, 
                method=decision.method
            )
            
            if numerical_sol.success:
                print(f"✓ Numerical integration successful ({numerical_sol.method})")
                print(f"  Time points: {len(numerical_sol.t)}")
                print(f"  States computed: {numerical_sol.y.shape[0]}")
                print()
                print("STATISTICS:")
                for key, value in numerical_sol.statistics.items():
                    print(f"  {key}: {value:.6f}")
            else:
                print(f"✗ Numerical integration failed: {numerical_sol.message}")
        
        print()
        
        # Step 4: Visualize
        print("Step 4: VISUALIZATION")
        print("-" * 80)
        
        fig = None

        if numerical_sol and numerical_sol.success:
            try:
                fig = self.visualizer.plot_numerical_solution(
                    numerical_sol,
                    equation,
                    title=f"{decision.equation_family}"
                )

                if save_plot:
                    path = plot_path if plot_path else "ode_solution.png"
                    fig.savefig(path, dpi=150, bbox_inches="tight")
                    print(f"✓ Plot saved to {path}")

                if show_plot:
                    import matplotlib.pyplot as plt
                    plt.show()

                print("✓ Visualization generated (Matplotlib figure)")

            except Exception as e:
                print(f"✗ Visualization failed: {e}")

        
        print()
        
        # Step 5: Generate explanation
        print("Step 5: EXPLANATION")
        print("-" * 80)
        explanation = self._generate_explanation(
            components, decision, symbolic_sol, numerical_sol
        )
        print(explanation)
        print()
        
        # Build classification dict
        classification = {
            'order': components.order,
            'linear': components.is_linear,
            'homogeneous': components.is_homogeneous,
            'family': decision.equation_family,
            'stiff': decision.stiffness_detected,
        }
        
        return CompleteSolution(
            equation=equation,
            classification=classification,
            routing_decision=decision,
            symbolic_solution=symbolic_sol,
            numerical_solution=numerical_sol,
            visualization=fig,
            explanation=explanation
        )

    
    def _generate_explanation(self,
                             components: ODEComponents,
                             decision: RoutingDecision,
                             symbolic_sol: Optional[SymbolicSolution],
                             numerical_sol: Optional[NumericalSolution]) -> str:
        """
        Generate structured explanation
        NO COMPUTATION HERE - only interpretation
        """
        
        explanation = []
        
        explanation.append("SOLUTION SUMMARY")
        explanation.append("="*70)
        explanation.append("")
        
        # Classification
        explanation.append("1. CLASSIFICATION")
        explanation.append(f"   • Order: {components.order}")
        explanation.append(f"   • Type: {'Linear' if components.is_linear else 'Nonlinear'}")
        explanation.append(f"   • {'Homogeneous' if components.is_homogeneous else 'Non-homogeneous'}")
        explanation.append(f"   • Family: {decision.equation_family}")
        explanation.append("")
        
        # Method
        explanation.append("2. SOLUTION METHOD")
        explanation.append(f"   • Solver: {decision.solver_type.title()}")
        explanation.append(f"   • Method: {decision.method}")
        explanation.append(f"   • Reason: {decision.reason}")
        if decision.stiffness_detected:
            explanation.append("   • ⚠ Stiff system - special handling required")
        explanation.append("")
        
        # Results
        if symbolic_sol:
            explanation.append("3. SYMBOLIC SOLUTION")
            explanation.append(f"   • Solution type: {symbolic_sol.solution_type}")
            if symbolic_sol.characteristic_roots:
                explanation.append(f"   • Roots: {symbolic_sol.characteristic_roots}")
            explanation.append(f"   • General solution computed ({len(symbolic_sol.derivation_steps)} steps)")
            explanation.append("")
        
        if numerical_sol and numerical_sol.success:
            explanation.append("3. NUMERICAL RESULTS" if not symbolic_sol else "4. NUMERICAL VERIFICATION")
            explanation.append(f"   • Time span: [{numerical_sol.t[0]:.1f}, {numerical_sol.t[-1]:.1f}]")
            explanation.append(f"   • Final value: x({numerical_sol.t[-1]:.1f}) = {numerical_sol.statistics['x_final']:.6f}")
            explanation.append(f"   • Range: [{numerical_sol.statistics['x_min']:.4f}, {numerical_sol.statistics['x_max']:.4f}]")
            
            if 'period_estimate' in numerical_sol.statistics:
                period = numerical_sol.statistics['period_estimate']
                freq = numerical_sol.statistics['frequency_estimate']
                explanation.append(f"   • Oscillation period: {period:.4f} (frequency: {freq:.4f} Hz)")
            
            explanation.append("")
        
        # Interpretation
        explanation.append("5. PHYSICAL INTERPRETATION")
        interp = self._interpret_system(components, decision, numerical_sol)
        for line in interp:
            explanation.append(f"   {line}")
        
        return "\n".join(explanation)
    
    def _interpret_system(self,
                         components: ODEComponents,
                         decision: RoutingDecision,
                         solution: Optional[NumericalSolution]) -> list:
        """Generate physical interpretation"""
        
        interpretation = []
        
        family = decision.equation_family.lower()
        
        if 'harmonic' in family:
            interpretation.append("• System exhibits harmonic oscillation")
            if 'damped' in family:
                interpretation.append("• Energy dissipates over time due to damping")
                if solution and 'period_estimate' in solution.statistics:
                    interpretation.append(f"• Damped oscillation with period ≈ {solution.statistics['period_estimate']:.2f}")
            else:
                interpretation.append("• Undamped - oscillations continue indefinitely")
        
        elif 'duffing' in family:
            interpretation.append("• Nonlinear oscillator with cubic restoring force")
            interpretation.append("• Can exhibit complex dynamics (chaos, limit cycles)")
            interpretation.append("• Amplitude-dependent frequency")
        
        elif 'van der pol' in family:
            interpretation.append("• Self-excited oscillator with nonlinear damping")
            interpretation.append("• Exhibits limit cycle behavior")
            interpretation.append("• Models biological oscillators, electronic circuits")
        
        elif 'pendulum' in family:
            interpretation.append("• Models pendulum motion")
            if components.is_linear:
                interpretation.append("• Small-angle approximation (linear)")
            else:
                interpretation.append("• Large-angle motion (nonlinear)")
        
        else:
            if components.is_linear:
                interpretation.append("• Linear system - superposition applies")
            else:
                interpretation.append("• Nonlinear system - rich dynamics possible")
            
            if solution and solution.success:
                x_range = solution.statistics['x_max'] - solution.statistics['x_min']
                if x_range < 0.1:
                    interpretation.append("• Solution approaches equilibrium")
                elif 'period_estimate' in solution.statistics:
                    interpretation.append("• Periodic behavior detected")
                else:
                    interpretation.append("• Non-periodic solution")
        
        return interpretation


def main():
    """Main demonstration"""
    
    solver = ODESolverSystem()
    
    # Example problems
    problems = [
        {
            'equation': "x'' + x = 0",
            'ic': {'x': 1, 'dx': 0},
            'description': "Simple Harmonic Oscillator"
        },
        {
            'equation': "x'' + 2*x' + x = 0",
            'ic': {'x': 1, 'dx': 0},
            'description': "Critically Damped Oscillator"
        },
        {
            'equation': "x'' + 0.2*x' + x + 0.1*x**3 = cos(t)",
            'ic': {'x': 1, 'dx': 0},
            'description': "Forced Duffing Oscillator"
        },
    ]
    
    for idx, problem in enumerate(problems, 1):
        print(f"\n\n{'='*80}")
        print(f"PROBLEM {idx}: {problem['description']}")
        print(f"{'='*80}\n")
        
        solution = solver.solve(
            equation=problem['equation'],
            initial_conditions=problem['ic'],
            time_span=(0, 50),
        )
        
        print("\n" + "="*80)
        print(f"PROBLEM {idx} COMPLETE")
        print("="*80)
        



if __name__ == '__main__':
    main()