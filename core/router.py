"""
Deterministic ODE Router
Makes solver selection decisions based on mathematical properties
NO LLM COMPUTATION INVOLVED
"""

from typing import Dict, Literal
from dataclasses import dataclass
from core.parser import ODEComponents


@dataclass
class RoutingDecision:
    """Solver routing decision"""
    solver_type: Literal['symbolic', 'numerical']
    method: str  # 'dsolve', 'RK45', 'Radau', 'BDF', etc.
    reason: str
    stiffness_detected: bool
    equation_family: str  # 'harmonic', 'damped', 'duffing', etc.
    symbolic_feasible: bool


class ODERouter:
    """Deterministic router for ODE solver selection"""
    
    def __init__(self):
        self.stiff_keywords = ['stiff', 'fast', 'chemical', 'reaction']
        self.known_stiff_patterns = [
            'van der pol',
            'robertson',
            'rober',
        ]
    
    def route(self, components: ODEComponents, 
              time_span: tuple = (0, 50),
              hint: str = None) -> RoutingDecision:
        """
        Route ODE to appropriate solver
        
        Decision tree:
        1. Is it linear and low-order? → Try symbolic
        2. Is it nonlinear? → Numerical
        3. Is it stiff? → Radau/BDF
        4. Default → RK45
        """
        
        # Detect stiffness
        stiff = self._detect_stiffness(components, hint)
        
        # Detect equation family
        family = self._classify_family(components)
        
        # Symbolic feasibility
        symbolic_possible = self._is_symbolic_feasible(components)
        
        # Make decision
        if symbolic_possible and components.order <= 2:
            return RoutingDecision(
                solver_type='symbolic',
                method='dsolve',
                reason='Linear ODE with constant coefficients - exact solution exists',
                stiffness_detected=False,
                equation_family=family,
                symbolic_feasible=True
            )
        
        elif stiff:
            return RoutingDecision(
                solver_type='numerical',
                method='Radau',
                reason='Stiff system detected - using implicit solver',
                stiffness_detected=True,
                equation_family=family,
                symbolic_feasible=False
            )
        
        else:
            return RoutingDecision(
                solver_type='numerical',
                method='RK45',
                reason='Nonlinear or complex ODE - numerical integration required',
                stiffness_detected=False,
                equation_family=family,
                symbolic_feasible=False
            )
    
    def _detect_stiffness(self, components: ODEComponents, hint: str = None) -> bool:
        """
        Detect if ODE is stiff
        
        Stiffness indicators:
        - Large coefficient ratios
        - Known stiff equations (Van der Pol with large μ)
        - User hint
        - Fast and slow timescales
        """
        
        # User hint
        if hint:
            hint_lower = hint.lower()
            if any(kw in hint_lower for kw in self.stiff_keywords):
                return True
            if any(pattern in hint_lower for pattern in self.known_stiff_patterns):
                return True
        
        # Coefficient analysis
        coeffs = components.coefficients
        if len(coeffs) >= 2:
            values = list(coeffs.values())
            if max(abs(v) for v in values if v != 0) / min(abs(v) for v in values if v != 0) > 100:
                return True
        
        # Van der Pol with large coefficient
        eq_lower = components.equation.lower()
        if 'van der pol' in eq_lower or ('x**2' in eq_lower and 'x\'' in eq_lower):
            # Check for large μ
            for val in coeffs.values():
                if abs(val) > 10:
                    return True
        
        return False
    
    def _classify_family(self, components: ODEComponents) -> str:
        """Classify ODE into known families"""
        
        eq = components.equation.lower()
        
        # Known families
        if 'van der pol' in eq:
            return 'Van der Pol oscillator'
        
        if 'duffing' in eq:
            return 'Duffing oscillator'
        
        if 'pendulum' in eq:
            return 'Pendulum'
        
        if 'lotka' in eq or 'volterra' in eq:
            return 'Lotka-Volterra'
        
        if 'lorenz' in eq:
            return 'Lorenz system'
        
        # Pattern-based classification
        if components.order == 2 and components.is_linear:
            if components.is_homogeneous:
                if 'x\'' not in eq or components.coefficients.get('x1', 0) == 0:
                    return 'Simple harmonic oscillator'
                else:
                    return 'Damped harmonic oscillator'
            else:
                return 'Driven harmonic oscillator'
        
        if components.order == 2 and 'x**3' in eq:
            return 'Duffing-type (cubic nonlinearity)'
        
        if components.order == 1:
            if components.is_linear:
                return 'Linear first-order'
            else:
                return 'Nonlinear first-order'
        
        return 'General ODE'
    
    def _is_symbolic_feasible(self, components: ODEComponents) -> bool:
        """
        Determine if symbolic solution is feasible
        
        Feasible if:
        - Linear
        - Constant coefficients
        - Order ≤ 2 (for now)
        - Standard forcing (sin, cos, exp, polynomial)
        """
        
        if not components.is_linear:
            return False
        
        if components.order > 3:
            return False
        
        # Check if coefficients are constant
        # (Advanced: could check if coefficients are functions of t)
        
        # Check forcing function complexity
        if components.forcing_function:
            forcing = components.forcing_function.lower()
            complex_forcing = ['**x', 'abs', 'log', 'tan']
            if any(cf in forcing for cf in complex_forcing):
                return False
        
        return True
    
    def get_solver_config(self, decision: RoutingDecision) -> Dict:
        """Get configuration parameters for chosen solver"""
        
        if decision.solver_type == 'symbolic':
            return {
                'method': 'dsolve',
                'simplify': True,
                'rational': False
            }
        
        else:
            config = {
                'method': decision.method,
                'rtol': 1e-8,
                'atol': 1e-10,
            }
            
            if decision.stiffness_detected:
                config.update({
                    'rtol': 1e-6,
                    'atol': 1e-8,
                    'max_step': 0.1
                })
            
            return config


def demo():
    """Demonstrate routing logic"""
    from core.parser import ODEParser
    
    parser = ODEParser()
    router = ODERouter()
    
    test_cases = [
        ("x'' + x = 0", None),
        ("x'' + 2*x' + x = 0", None),
        ("x'' + 0.2*x' + x + 0.1*x**3 = cos(t)", None),
        ("x'' + 1000*x' + x = 0", "stiff system"),
    ]
    
    for eq, hint in test_cases:
        print(f"\n{'='*70}")
        print(f"Equation: {eq}")
        if hint:
            print(f"Hint: {hint}")
        print('='*70)
        
        components = parser.parse(eq)
        decision = router.route(components, hint=hint)
        
        print(f"Solver: {decision.solver_type} ({decision.method})")
        print(f"Reason: {decision.reason}")
        print(f"Family: {decision.equation_family}")
        print(f"Stiff: {decision.stiffness_detected}")
        print(f"Symbolic feasible: {decision.symbolic_feasible}")


if __name__ == '__main__':
    demo()