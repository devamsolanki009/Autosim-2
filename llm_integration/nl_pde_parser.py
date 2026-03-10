"""
Natural Language PDE Parser
Inspired by CodePDE paper (arXiv:2505.08783)

Converts natural language descriptions to mathematical equations
and generates custom numerical solvers
"""

from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
import re
from llm_integration.deepseek_interface import DeepSeekInterface


@dataclass
class PDESpecification:
    """Structured PDE specification extracted from natural language"""
    equation: str
    equation_type: str  # 'heat', 'wave', 'poisson', 'custom'
    domain: str  # '1D', '2D', '3D'
    boundary_conditions: Dict[str, str]
    initial_conditions: Optional[Dict[str, str]]
    parameters: Dict[str, float]
    natural_language: str
    confidence: float


class NaturalLanguagePDEParser:
    """
    Parse natural language PDE descriptions
    Inspired by CodePDE approach
    """
    
    def __init__(self, llm: Optional[DeepSeekInterface] = None):
        """
        Initialize parser
        
        Args:
            llm: DeepSeek interface (creates new one if None)
        """
        self.llm = llm or DeepSeekInterface()
        
        # Known PDE patterns
        self.pde_patterns = {
            'heat': r'heat equation|diffusion|thermal|temperature',
            'wave': r'wave equation|vibration|acoustic|string',
            'poisson': r'poisson|laplace|potential|electrostatic',
            'advection': r'advection|transport|flow',
            'burger': r'burger|burgers|shock',
            'diffusion': r'diffusion|fick',
        }
    
    def parse_natural_language(self, description: str) -> PDESpecification:
        """
        Parse natural language description to PDE specification
        
        Args:
            description: Natural language description of PDE
        
        Returns:
            PDESpecification object
        """
        
        # Build prompt for LLM
        system_prompt = """You are an expert in partial differential equations and numerical methods.
Given a natural language description of a PDE problem, extract:
1. The mathematical equation (use standard notation: u_t, u_xx, etc.)
2. Equation type (heat, wave, poisson, advection, etc.)
3. Spatial domain (1D, 2D, or 3D)
4. Boundary conditions
5. Initial conditions (if time-dependent)
6. Physical parameters

Output ONLY a JSON object with these fields:
{
  "equation": "mathematical equation",
  "type": "equation type",
  "domain": "1D/2D/3D",
  "boundary_conditions": {"location": "condition"},
  "initial_conditions": {"variable": "condition"},
  "parameters": {"name": value},
  "confidence": 0.0-1.0
}"""
        
        prompt = f"""Extract PDE specification from this description:

"{description}"

JSON:"""
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=1000
        )
        
        if response.success:
            try:
                # Extract JSON from response
                content = response.content.strip()
                
                # Try to find JSON block
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    import json
                    spec_dict = json.loads(json_match.group(0))
                    
                    return PDESpecification(
                        equation=spec_dict.get('equation', 'unknown'),
                        equation_type=spec_dict.get('type', 'custom'),
                        domain=spec_dict.get('domain', '1D'),
                        boundary_conditions=spec_dict.get('boundary_conditions', {}),
                        initial_conditions=spec_dict.get('initial_conditions'),
                        parameters=spec_dict.get('parameters', {}),
                        natural_language=description,
                        confidence=spec_dict.get('confidence', 0.5)
                    )
                else:
                    # Fallback: manual parsing
                    return self._fallback_parse(description)
            
            except Exception as e:
                print(f"JSON parsing failed: {e}")
                return self._fallback_parse(description)
        else:
            return self._fallback_parse(description)
    
    def _fallback_parse(self, description: str) -> PDESpecification:
        """Fallback parsing using pattern matching"""
        
        desc_lower = description.lower()
        
        # Detect equation type
        eq_type = 'custom'
        for pde_type, pattern in self.pde_patterns.items():
            if re.search(pattern, desc_lower):
                eq_type = pde_type
                break
        
        # Detect domain
        domain = '1D'
        if '2d' in desc_lower or 'two-dimensional' in desc_lower or 'plane' in desc_lower:
            domain = '2D'
        elif '3d' in desc_lower or 'three-dimensional' in desc_lower or 'volume' in desc_lower:
            domain = '3D'
        
        # Generate standard equation
        equation = self._get_standard_equation(eq_type, domain)
        
        return PDESpecification(
            equation=equation,
            equation_type=eq_type,
            domain=domain,
            boundary_conditions={'default': 'Dirichlet u=0'},
            initial_conditions={'u': 'u(x,0) = u0(x)'},
            parameters={'alpha': 1.0},
            natural_language=description,
            confidence=0.3
        )
    
    def _get_standard_equation(self, eq_type: str, domain: str) -> str:
        """Get standard form of known equations"""
        
        standard_forms = {
            'heat': {
                '1D': 'u_t = alpha * u_xx',
                '2D': 'u_t = alpha * (u_xx + u_yy)',
                '3D': 'u_t = alpha * (u_xx + u_yy + u_zz)'
            },
            'wave': {
                '1D': 'u_tt = c^2 * u_xx',
                '2D': 'u_tt = c^2 * (u_xx + u_yy)',
                '3D': 'u_tt = c^2 * (u_xx + u_yy + u_zz)'
            },
            'poisson': {
                '1D': 'u_xx = f(x)',
                '2D': 'u_xx + u_yy = f(x,y)',
                '3D': 'u_xx + u_yy + u_zz = f(x,y,z)'
            }
        }
        
        if eq_type in standard_forms and domain in standard_forms[eq_type]:
            return standard_forms[eq_type][domain]
        else:
            return f'{eq_type} equation in {domain}'
    
    def generate_solver_code(self, spec: PDESpecification) -> str:
        """
        Generate numerical solver code for PDE
        Inspired by CodePDE approach
        
        Args:
            spec: PDE specification
        
        Returns:
            Python code for solver
        """
        
        description = f"""Generate a complete Python solver for the following PDE:

Equation: {spec.equation}
Type: {spec.equation_type}
Domain: {spec.domain}
Boundary Conditions: {spec.boundary_conditions}
Initial Conditions: {spec.initial_conditions}
Parameters: {spec.parameters}

Original description: "{spec.natural_language}"

Requirements:
1. Use finite difference or finite element method
2. Include time-stepping if time-dependent
3. Apply boundary conditions correctly
4. Return solution as numpy array
5. Include visualization with matplotlib
6. Add docstrings and comments

Generate complete, runnable Python code."""
        
        response = self.llm.generate_code(description)
        
        if response.success:
            return response.content
        else:
            return self._generate_template_solver(spec)
    
    def _generate_template_solver(self, spec: PDESpecification) -> str:
        """Generate template solver code"""
        
        return f'''"""
Auto-generated PDE Solver
Equation: {spec.equation}
Type: {spec.equation_type}
Domain: {spec.domain}
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve


def solve_pde(nx=100, nt=1000, L=1.0, T=1.0):
    """
    Solve PDE: {spec.equation}
    
    Args:
        nx: Number of spatial grid points
        nt: Number of time steps
        L: Spatial domain length
        T: Total time
    
    Returns:
        x: Spatial coordinates
        t: Time coordinates  
        u: Solution array
    """
    
    # Setup grid
    x = np.linspace(0, L, nx)
    t = np.linspace(0, T, nt)
    dx = x[1] - x[0]
    dt = t[1] - t[0]
    
    # Initialize solution
    u = np.zeros((nt, nx))
    
    # Set initial condition
    u[0, :] = np.sin(np.pi * x / L)  # Example IC
    
    # Apply boundary conditions
    u[:, 0] = 0  # Left boundary
    u[:, -1] = 0  # Right boundary
    
    # Time stepping (simple forward Euler for demo)
    alpha = {spec.parameters.get('alpha', 1.0)}
    r = alpha * dt / dx**2
    
    for n in range(nt-1):
        for i in range(1, nx-1):
            # Finite difference approximation
            u[n+1, i] = u[n, i] + r * (u[n, i+1] - 2*u[n, i] + u[n, i-1])
    
    return x, t, u


def visualize_solution(x, t, u):
    """Visualize PDE solution"""
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Space-time plot
    X, T = np.meshgrid(x, t)
    im = ax1.contourf(X, T, u, levels=20, cmap='viridis')
    ax1.set_xlabel('Space (x)')
    ax1.set_ylabel('Time (t)')
    ax1.set_title('Solution: {spec.equation}')
    plt.colorbar(im, ax=ax1)
    
    # Snapshots at different times
    for i in range(0, len(t), len(t)//5):
        ax2.plot(x, u[i, :], label=f't={t[i]:.2f}')
    ax2.set_xlabel('Space (x)')
    ax2.set_ylabel('u(x,t)')
    ax2.set_title('Solution Snapshots')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


if __name__ == '__main__':
    print("Solving PDE: {spec.equation}")
    print("Type: {spec.equation_type}")
    print("Domain: {spec.domain}")
    print()
    
    # Solve
    x, t, u = solve_pde()
    
    print(f"Solution computed: {{u.shape}}")
    print(f"Domain: x ∈ [{{x[0]:.2f}}, {{x[-1]:.2f}}]")
    print(f"Time: t ∈ [{{t[0]:.2f}}, {{t[-1]:.2f}}]")
    print()
    
    # Visualize
    fig = visualize_solution(x, t, u)
    plt.savefig('pde_solution.png', dpi=150, bbox_inches='tight')
    print("Solution saved to pde_solution.png")
    plt.show()
'''


def demo():
    """Demonstrate natural language PDE parsing"""
    
    print("="*80)
    print("NATURAL LANGUAGE PDE PARSER (CodePDE-inspired)")
    print("="*80)
    print()
    
    # Initialize
    parser = NaturalLanguagePDEParser()
    
    # Check LLM connection
    if not parser.llm.check_connection():
        print("⚠ Warning: Cannot connect to DeepSeek")
        print("   Using fallback pattern-based parsing")
    
    print()
    
    # Test cases
    test_descriptions = [
        "Solve the 1D heat equation with Dirichlet boundary conditions",
        "Model heat diffusion in a 2D rectangular plate with insulated edges",
        "Solve wave propagation in a vibrating string fixed at both ends",
        "Find steady-state temperature distribution (Poisson equation) in 2D"
    ]
    
    for i, desc in enumerate(test_descriptions, 1):
        print(f"Test {i}: {desc}")
        print("-" * 80)
        
        # Parse description
        spec = parser.parse_natural_language(desc)
        
        print(f"✓ Parsed successfully")
        print(f"  Equation: {spec.equation}")
        print(f"  Type: {spec.equation_type}")
        print(f"  Domain: {spec.domain}")
        print(f"  Confidence: {spec.confidence:.2f}")
        print()
    
    # Generate solver for first test case
    print("="*80)
    print("GENERATING SOLVER CODE")
    print("="*80)
    print()
    
    spec = parser.parse_natural_language(test_descriptions[0])
    print(f"Description: {test_descriptions[0]}")
    print(f"Equation: {spec.equation}")
    print()
    print("Generating solver code...")
    
    code = parser.generate_solver_code(spec)
    
    print("✓ Code generated")
    print()
    print("Generated Code (first 30 lines):")
    print("-" * 80)
    for i, line in enumerate(code.split('\n')[:30], 1):
        print(f"{i:3d} | {line}")
    
    lines = code.split('\n')
    extra_lines = len(lines) - 30

    if len(lines) > 30:
        print(f"... ({extra_lines} more lines)")
    
    print()
    print("="*80)


if __name__ == '__main__':
    demo()