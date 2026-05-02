"""
Symbolic ODE Solver with Step-by-Step Derivation
Generates mathematical steps for educational purposes
"""

import sympy as sp
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from core.parser import ODEComponents


@dataclass
class DerivationStep:
    """Single step in symbolic derivation"""
    step_number: int
    description: str
    equation: str
    latex: str


@dataclass
class SymbolicSolution:
    """Complete symbolic solution with derivation"""
    general_solution: sp.Expr
    particular_solution: Optional[sp.Expr]
    derivation_steps: List[DerivationStep]
    solution_type: str  # 'real', 'complex', 'repeated'
    characteristic_roots: List[complex]


class SymbolicSolver:
    """Solve ODEs symbolically and generate derivations"""
    
    def __init__(self):
        self.t = sp.Symbol('t', real=True, positive=True)
        self.x = sp.Function('x')
        self.C1 = sp.Symbol('C1', real=True)
        self.C2 = sp.Symbol('C2', real=True)
    
    def solve(self, components: ODEComponents, 
              initial_conditions: Dict[str, float] = None) -> SymbolicSolution:
        """
        Solve ODE symbolically with step-by-step derivation
        """
        
        if components.order == 1:
            return self._solve_first_order(components, initial_conditions)
        elif components.order == 2:
            return self._solve_second_order(components, initial_conditions)
        else:
            raise NotImplementedError(f"Order {components.order} not implemented")
    
    def _solve_second_order(self, components: ODEComponents, 
                           initial_conditions: Dict[str, float] = None) -> SymbolicSolution:
        """
        Solve second-order linear ODE with constant coefficients
        
        General form: a*x'' + b*x' + c*x = f(t)
        """
        
        steps = []
        step_num = 1
        
        # Step 1: State the ODE
        steps.append(DerivationStep(
            step_number=step_num,
            description="Given ODE",
            equation=components.equation,
            latex=self._to_latex(components.equation)
        ))
        step_num += 1
        
        # Extract coefficients
        a = components.coefficients.get('x2', 1.0)
        b = components.coefficients.get('x1', 0.0)
        c = components.coefficients.get('x0', 0.0)
        
        # Step 2: For homogeneous, assume exponential solution
        if components.is_homogeneous:
            steps.append(DerivationStep(
                step_number=step_num,
                description="Assume solution of the form",
                equation="x(t) = exp(r*t)",
                latex=r"x(t) = e^{rt}"
            ))
            step_num += 1
            
            # Step 3: Substitute into ODE
            steps.append(DerivationStep(
                step_number=step_num,
                description="Substitute into the ODE",
                equation=f"{a}*r^2*exp(r*t) + {b}*r*exp(r*t) + {c}*exp(r*t) = 0",
                latex=f"{a}r^2 e^{{rt}} + {b}r e^{{rt}} + {c} e^{{rt}} = 0"
            ))
            step_num += 1
            
            # Step 4: Characteristic equation
            char_eq = f"{a}*r^2 + {b}*r + {c} = 0"
            steps.append(DerivationStep(
                step_number=step_num,
                description="Characteristic equation (divide by exp(r*t))",
                equation=char_eq,
                latex=f"{a}r^2 + {b}r + {c} = 0"
            ))
            step_num += 1
            
            # Step 5: Solve characteristic equation
            r = sp.Symbol('r')
            char_poly = a * r**2 + b * r + c
            roots = sp.solve(char_poly, r)
            
            steps.append(DerivationStep(
                step_number=step_num,
                description="Solve for r using quadratic formula",
                equation=f"r = {roots}",
                latex=self._roots_to_latex(roots, a, b, c)
            ))
            step_num += 1
            
            # Classify roots
            solution_type, general_sol = self._classify_roots_and_build_solution(roots, a, b, c)
            
            # Step 6: General solution
            steps.append(DerivationStep(
                step_number=step_num,
                description=f"General solution ({solution_type} roots)",
                equation=str(general_sol),
                latex=sp.latex(general_sol)
            ))
            step_num += 1
            
            # If initial conditions provided, solve for constants
            particular = None
            if initial_conditions:
                particular, const_steps = self._apply_initial_conditions(
                    general_sol, initial_conditions, step_num
                )
                steps.extend(const_steps)
            
            return SymbolicSolution(
                general_solution=general_sol,
                particular_solution=particular,
                derivation_steps=steps,
                solution_type=solution_type,
                characteristic_roots=roots
            )
        
        else:
            # Non-homogeneous: use SymPy's dsolve
            a_sym = sp.sympify(a)
            b_sym = sp.sympify(b)
            c_sym = sp.sympify(c)
            forcing_sym = sp.sympify(
                str(components.forcing_function),
                locals={'t': self.t, 'sin': sp.sin, 'cos': sp.cos, 'exp': sp.exp}
            )
            ode_eq = sp.Eq(
                a_sym * sp.diff(self.x(self.t), self.t, 2) +
                b_sym * sp.diff(self.x(self.t), self.t) +
                c_sym * self.x(self.t),
                forcing_sym
            )
            
            solution = sp.dsolve(ode_eq, self.x(self.t))
            
            steps.append(DerivationStep(
                step_number=step_num,
                description="Solution obtained via method of undetermined coefficients",
                equation=str(solution),
                latex=sp.latex(solution)
            ))
            
            return SymbolicSolution(
                general_solution=solution.rhs,
                particular_solution=None,
                derivation_steps=steps,
                solution_type='non-homogeneous',
                characteristic_roots=[]
            )
    
    def _classify_roots_and_build_solution(self, roots: List, a: float, b: float, c: float) -> Tuple[str, sp.Expr]:
        """
        Classify roots and build general solution
        
        Cases:
        1. Real distinct: x = C1*exp(r1*t) + C2*exp(r2*t)
        2. Real repeated: x = (C1 + C2*t)*exp(r*t)
        3. Complex conjugate: x = exp(α*t)*(C1*cos(β*t) + C2*sin(β*t))
        """
        
        if len(roots) == 2:
            r1, r2 = roots
            
            # Check if roots are equal (repeated)
            if sp.simplify(r1 - r2) == 0:
                solution_type = "repeated real"
                general_sol = (self.C1 + self.C2 * self.t) * sp.exp(r1 * self.t)
            
            # Check if complex
            elif sp.im(r1) != 0:
                solution_type = "complex conjugate"
                alpha = sp.re(r1)
                beta = sp.im(r1)
                general_sol = sp.exp(alpha * self.t) * (
                    self.C1 * sp.cos(beta * self.t) + 
                    self.C2 * sp.sin(beta * self.t)
                )
            
            else:
                solution_type = "real distinct"
                general_sol = self.C1 * sp.exp(r1 * self.t) + self.C2 * sp.exp(r2 * self.t)
        
        else:
            # Single root (shouldn't happen for 2nd order)
            solution_type = "single root"
            general_sol = self.C1 * sp.exp(roots[0] * self.t)
        
        return solution_type, general_sol
    
    def _apply_initial_conditions(self, general_sol: sp.Expr, 
                                  ic: Dict[str, float],
                                  start_step: int) -> Tuple[sp.Expr, List[DerivationStep]]:
        """Apply initial conditions to find particular solution"""
        
        steps = []
        step_num = start_step
        
        # Get x(0) and x'(0)
        x0 = ic.get('x', 0)
        dx0 = ic.get('dx', 0)
        
        steps.append(DerivationStep(
            step_number=step_num,
            description="Apply initial conditions",
            equation=f"x(0) = {x0}, x'(0) = {dx0}",
            latex=f"x(0) = {x0}, \\quad x'(0) = {dx0}"
        ))
        step_num += 1
        
        # Evaluate at t=0
        sol_at_0 = general_sol.subs(self.t, 0)
        eq1 = sp.Eq(sol_at_0, x0)
        
        steps.append(DerivationStep(
            step_number=step_num,
            description="From x(0) = " + str(x0),
            equation=str(eq1),
            latex=sp.latex(eq1)
        ))
        step_num += 1
        
        # Derivative at t=0
        general_sol_prime = sp.diff(general_sol, self.t)
        sol_prime_at_0 = general_sol_prime.subs(self.t, 0)
        eq2 = sp.Eq(sol_prime_at_0, dx0)
        
        steps.append(DerivationStep(
            step_number=step_num,
            description="From x'(0) = " + str(dx0),
            equation=str(eq2),
            latex=sp.latex(eq2)
        ))
        step_num += 1
        
        # Solve system
        try:
            constants = sp.solve([eq1, eq2], [self.C1, self.C2])
            
            steps.append(DerivationStep(
                step_number=step_num,
                description="Solve for constants",
                equation=f"C1 = {constants[self.C1]}, C2 = {constants[self.C2]}",
                latex=f"C_1 = {sp.latex(constants[self.C1])}, \\quad C_2 = {sp.latex(constants[self.C2])}"
            ))
            step_num += 1
            
            # Substitute back
            particular = general_sol.subs(constants)
            
            steps.append(DerivationStep(
                step_number=step_num,
                description="Particular solution",
                equation=str(particular),
                latex=sp.latex(particular)
            ))
            
            return particular, steps
        
        except Exception as e:
            # Could not solve
            steps.append(DerivationStep(
                step_number=step_num,
                description="Could not solve for constants symbolically",
                equation="See numerical solution",
                latex="\\text{See numerical solution}"
            ))
            return general_sol, steps
    
    def _solve_first_order(self, components: ODEComponents,
                          initial_conditions: Dict[str, float] = None) -> SymbolicSolution:
        """Solve first-order linear ODE"""
        
        steps = []
        
        # Use SymPy for first-order
        ode_eq = components.symbolic_form
        solution = sp.dsolve(ode_eq, self.x(self.t))
        
        steps.append(DerivationStep(
            step_number=1,
            description="Solution",
            equation=str(solution),
            latex=sp.latex(solution)
        ))
        
        return SymbolicSolution(
            general_solution=solution.rhs,
            particular_solution=None,
            derivation_steps=steps,
            solution_type='first-order',
            characteristic_roots=[]
        )
    
    def _to_latex(self, equation: str) -> str:
        """Convert equation string to LaTeX"""
        latex = equation
        latex = latex.replace("x''", r"\ddot{x}")
        latex = latex.replace("x'", r"\dot{x}")
        latex = latex.replace('**', '^')
        latex = latex.replace('*', r'\cdot ')
        return latex
    
    def _roots_to_latex(self, roots: List, a: float, b: float, c: float) -> str:
        """Format roots in LaTeX using quadratic formula"""
        
        if len(roots) == 2:
            discriminant = b**2 - 4*a*c
            
            if discriminant >= 0:
                return f"r = \\frac{{-{b} \\pm \\sqrt{{{discriminant}}}}}{{{2*a}}}"
            else:
                return f"r = \\frac{{-{b} \\pm i\\sqrt{{{abs(discriminant)}}}}}{{{2*a}}}"
        
        return str(roots)


def demo():
    """Demonstrate symbolic solver"""
    from core.parser import ODEParser
    
    parser = ODEParser()
    solver = SymbolicSolver()
    
    # Test case: damped harmonic oscillator
    eq = "x'' + 2*x' + x = 0"
    ic = {'x': 1, 'dx': 0}
    
    print(f"Solving: {eq}")
    print(f"Initial conditions: {ic}\n")
    
    components = parser.parse(eq)
    solution = solver.solve(components, ic)
    
    print("STEP-BY-STEP DERIVATION")
    print("=" * 70)
    
    for step in solution.derivation_steps:
        print(f"\nStep {step.step_number}: {step.description}")
        print(f"  {step.equation}")
        print(f"  LaTeX: {step.latex}")
    
    print("\n" + "=" * 70)
    print(f"Solution type: {solution.solution_type}")
    print(f"Roots: {solution.characteristic_roots}")


if __name__ == '__main__':
    demo()