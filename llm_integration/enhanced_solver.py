"""
LLM-Enhanced ODE/PDE Solver System
Capstone Project - Advanced Integration

Combines:
1. Original zero-hallucination ODE solver
2. DeepSeek LLM for natural language understanding
3. CodePDE-inspired PDE code generation
4. Intelligent equation interpretation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, Optional, Tuple, Union
from dataclasses import dataclass
from main import ODESolverSystem, CompleteSolution
from llm_integration.deepseek_interface import DeepSeekInterface
from llm_integration.nl_pde_parser import NaturalLanguagePDEParser, PDESpecification


@dataclass
class EnhancedSolution:
    """Complete solution with LLM enhancements"""
    # Original ODE solution
    ode_solution: Optional[CompleteSolution]
    
    # PDE specification (if applicable)
    pde_spec: Optional[PDESpecification]
    
    # LLM-generated content
    natural_language_explanation: str
    generated_solver_code: Optional[str]
    physical_interpretation: str
    
    # Metadata
    used_llm: bool
    llm_model: str
    processing_mode: str  # 'ode', 'pde', 'hybrid'


class LLMEnhancedSolver:
    """
    Advanced solver with LLM integration
    
    Features:
    - Natural language input parsing
    - Automatic ODE/PDE detection
    - Custom solver code generation
    - Enhanced explanations
    - Zero hallucination for numerical computation
    """
    
    def __init__(self, use_llm: bool = True):
        """
        Initialize enhanced solver
        
        Args:
            use_llm: Whether to use LLM features
        """
        # Core solvers
        self.ode_solver = ODESolverSystem()
        
        # LLM components
        self.use_llm = use_llm
        if use_llm:
            self.llm = DeepSeekInterface()
            self.pde_parser = NaturalLanguagePDEParser(self.llm)
            self.llm_available = self.llm.check_connection()
            
            if not self.llm_available:
                print("⚠ Warning: DeepSeek not available. LLM features disabled.")
                print("   Make sure Ollama is running: ollama serve")
                self.use_llm = False
        else:
            self.llm_available = False
    
    def solve_from_natural_language(self,
                                    description: str,
                                    initial_conditions: Optional[Dict[str, float]] = None,
                                    time_span: Tuple[float, float] = (0, 20)) -> EnhancedSolution:
        """
        Solve from natural language description
        
        This is the main innovation - natural language to solution
        
        Args:
            description: Natural language description
            initial_conditions: Initial conditions (if needed)
            time_span: Time span for solution
        
        Returns:
            EnhancedSolution with all results
        """
        
        print("="*80)
        print("LLM-ENHANCED SOLVER - NATURAL LANGUAGE MODE")
        print("="*80)
        print()
        print(f"Input: \"{description}\"")
        print()
        
        # Step 1: Determine if ODE or PDE
        problem_type = self._classify_problem(description)
        print(f"Problem Classification: {problem_type}")
        print()
        
        if problem_type == 'ODE':
            return self._solve_ode_from_nl(description, initial_conditions, time_span)
        elif problem_type == 'PDE':
            return self._solve_pde_from_nl(description)
        else:
            # Hybrid or unclear - try both
            return self._solve_hybrid(description, initial_conditions, time_span)
    
    def solve_with_explanation(self,
                               equation: str,
                               initial_conditions: Dict[str, float],
                               time_span: Tuple[float, float] = (0, 20)) -> EnhancedSolution:
        """
        Solve equation with LLM-enhanced explanations
        
        Args:
            equation: Mathematical equation
            initial_conditions: Initial conditions
            time_span: Time span
        
        Returns:
            EnhancedSolution
        """
        
        print("="*80)
        print("LLM-ENHANCED SOLVER - EQUATION MODE")
        print("="*80)
        print()
        
        # Solve using core system
        ode_solution = self.ode_solver.solve(
            equation=equation,
            initial_conditions=initial_conditions,
            time_span=time_span,
            save_plot=False
        )
        
        # Generate LLM enhancements
        if self.use_llm and self.llm_available:
            print("\nGenerating LLM enhancements...")
            
            # Get detailed explanation
            explanation = self.llm.explain_equation(equation)
            nl_explanation = explanation.content if explanation.success else "Explanation unavailable"
            
            # Get physical interpretation
            interpretation = self._generate_interpretation(equation, ode_solution)
            
            return EnhancedSolution(
                ode_solution=ode_solution,
                pde_spec=None,
                natural_language_explanation=nl_explanation,
                generated_solver_code=None,
                physical_interpretation=interpretation,
                used_llm=True,
                llm_model="deepseek-coder:6.7b",
                processing_mode='ode'
            )
        else:
            return EnhancedSolution(
                ode_solution=ode_solution,
                pde_spec=None,
                natural_language_explanation="LLM unavailable",
                generated_solver_code=None,
                physical_interpretation=ode_solution.explanation,
                used_llm=False,
                llm_model="none",
                processing_mode='ode'
            )
    
    def _classify_problem(self, description: str) -> str:
        """Classify problem as ODE, PDE, or hybrid"""
        
        desc_lower = description.lower()
        
        # PDE indicators
        pde_keywords = ['partial', 'heat', 'wave', 'laplace', 'poisson', 
                       'diffusion', 'spatial', '2d', '3d', 'plate', 'membrane']
        
        # ODE indicators  
        ode_keywords = ['ordinary', 'oscillator', 'harmonic', 'damped',
                       'pendulum', 'trajectory', 'time evolution']
        
        pde_score = sum(1 for kw in pde_keywords if kw in desc_lower)
        ode_score = sum(1 for kw in ode_keywords if kw in desc_lower)
        
        if pde_score > ode_score:
            return 'PDE'
        elif ode_score > pde_score:
            return 'ODE'
        else:
            return 'HYBRID'
    
    def _solve_ode_from_nl(self, 
                          description: str,
                          initial_conditions: Optional[Dict[str, float]],
                          time_span: Tuple[float, float]) -> EnhancedSolution:
        """Solve ODE from natural language"""
        
        print("MODE: Ordinary Differential Equation")
        print()
        
        # Use LLM to extract equation
        if self.use_llm and self.llm_available:
            equation = self._extract_ode_equation(description)
            print(f"Extracted Equation: {equation}")
        else:
            # Fallback
            equation = self._extract_ode_fallback(description)
            print(f"Extracted Equation (fallback): {equation}")
        
        # Set default IC if not provided
        if initial_conditions is None:
            initial_conditions = {'x': 1, 'dx': 0}
        
        print(f"Initial Conditions: {initial_conditions}")
        print()
        
        # Solve
        return self.solve_with_explanation(equation, initial_conditions, time_span)
    
    def _solve_pde_from_nl(self, description: str) -> EnhancedSolution:
        """Solve PDE from natural language"""
        
        print("MODE: Partial Differential Equation")
        print()
        
        if not self.use_llm or not self.llm_available:
            print("⚠ LLM required for PDE solving. Fallback not available.")
            return EnhancedSolution(
                ode_solution=None,
                pde_spec=None,
                natural_language_explanation="LLM required for PDE mode",
                generated_solver_code=None,
                physical_interpretation="",
                used_llm=False,
                llm_model="none",
                processing_mode='pde'
            )
        
        # Parse PDE specification
        print("Parsing PDE specification...")
        pde_spec = self.pde_parser.parse_natural_language(description)
        
        print(f"✓ Equation: {pde_spec.equation}")
        print(f"  Type: {pde_spec.equation_type}")
        print(f"  Domain: {pde_spec.domain}")
        print(f"  Confidence: {pde_spec.confidence:.2f}")
        print()
        
        # Generate solver code
        print("Generating numerical solver code...")
        solver_code = self.pde_parser.generate_solver_code(pde_spec)
        
        print(f"✓ Generated {len(solver_code.split(chr(10)))} lines of code")
        print()
        
        # Generate explanation
        explanation_prompt = f"""Explain this PDE problem in detail:

Equation: {pde_spec.equation}
Type: {pde_spec.equation_type}
Domain: {pde_spec.domain}

Provide:
1. Physical meaning
2. Applications
3. Solution approach
4. Key properties"""
        
        explanation_resp = self.llm.generate(explanation_prompt, temperature=0.3)
        explanation = explanation_resp.content if explanation_resp.success else "Explanation unavailable"
        
        return EnhancedSolution(
            ode_solution=None,
            pde_spec=pde_spec,
            natural_language_explanation=explanation,
            generated_solver_code=solver_code,
            physical_interpretation=f"PDE: {pde_spec.equation_type} in {pde_spec.domain}",
            used_llm=True,
            llm_model="deepseek-coder:6.7b",
            processing_mode='pde'
        )
    
    def _solve_hybrid(self,
                     description: str,
                     initial_conditions: Optional[Dict[str, float]],
                     time_span: Tuple[float, float]) -> EnhancedSolution:
        """Handle hybrid or unclear cases"""
        
        print("MODE: Hybrid (attempting ODE first)")
        print()
        
        # Try ODE first
        return self._solve_ode_from_nl(description, initial_conditions, time_span)
    
    def _extract_ode_equation(self, description: str) -> str:
        """Extract ODE equation from natural language using LLM"""
        
        system_prompt = """You are an expert in differential equations.

Extract ONLY the final differential equation.

Output format must be EXACTLY one line like this:

x'' + 2*x' + x = 0

Rules:
- No explanation
- No extra text
- No multiple equations
- One line only
"""
        
        prompt = f"""Extract the differential equation from:

"{description}"

Equation:"""
        
        response = self.llm.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=200
        )
        
        if response.success:
            raw_output = response.content.strip()

            # Step 1: Split into lines
            lines = raw_output.split('\n')

            # Step 2: Find first line containing '='
            clean_equation = None
            for line in lines:
                line = line.strip()
                if '=' in line:
                    clean_equation = line
                    break

            # If no valid equation found → fallback
            if clean_equation is None:
                return self._extract_ode_fallback(description)

            # Step 3: Remove prefixes like "Equation:"
            if ':' in clean_equation:
                clean_equation = clean_equation.split(':')[-1].strip()

            # Step 4: Remove trailing explanations after period
            clean_equation = clean_equation.split('.')[0].strip()

            return clean_equation
        else:
            return self._extract_ode_fallback(description)
    
    def _extract_ode_fallback(self, description: str) -> str:
        """Fallback equation extraction using patterns"""
        
        desc_lower = description.lower()
        
        # Pattern matching for common ODEs
        if 'harmonic' in desc_lower and 'damped' not in desc_lower:
            return "x'' + x = 0"
        elif 'damped' in desc_lower:
            return "x'' + 2*x' + x = 0"
        elif 'duffing' in desc_lower:
            return "x'' + 0.2*x' + x + 0.1*x**3 = cos(t)"
        elif 'van der pol' in desc_lower:
            return "x'' - 0.5*(1-x**2)*x' + x = 0"
        else:
            return "x'' + x' + x = 0"  # Generic damped oscillator
    
    def _generate_interpretation(self, equation: str, solution: CompleteSolution) -> str:
        """Generate enhanced physical interpretation using LLM"""
        
        if not self.use_llm or not self.llm_available:
            return solution.explanation
        
        prompt = f"""Provide a detailed physical interpretation of this differential equation solution:

Equation: {equation}
Classification: {solution.classification}
Solver Method: {solution.routing_decision.method}

Include:
1. Physical system being modeled
2. Meaning of the solution
3. Real-world applications
4. Key insights

Interpretation:"""
        
        response = self.llm.generate(prompt, temperature=0.3, max_tokens=800)
        
        if response.success:
            return response.content
        else:
            return solution.explanation


def demo_capstone_features():
    """
    Demonstrate capstone project features
    Advanced LLM integration
    """
    
    print("\n" + "🎓 "*40)
    print("CAPSTONE PROJECT DEMONSTRATION")
    print("LLM-Enhanced ODE/PDE Solver System")
    print("🎓 "*40 + "\n")
    
    # Initialize enhanced solver
    solver = LLMEnhancedSolver(use_llm=True)
    
    if not solver.llm_available:
        print("\n⚠ WARNING: DeepSeek not available!")
        print("Please ensure Ollama is running with deepseek-coder:6.7b")
        print("Command: ollama serve")
        print("\nContinuing with limited functionality...\n")
    
    # Test Case 1: Natural Language ODE
    print("\n" + "="*80)
    print("TEST 1: NATURAL LANGUAGE ODE INPUT")
    print("="*80 + "\n")
    
    nl_description = "Model a damped harmonic oscillator with critical damping"
    solution1 = solver.solve_from_natural_language(
        description=nl_description,
        initial_conditions={'x': 1, 'dx': 0},
        time_span=(0, 20)
    )
    
    print("\n📊 RESULTS:")
    print(f"  Mode: {solution1.processing_mode}")
    print(f"  Used LLM: {solution1.used_llm}")
    if solution1.ode_solution:
        print(f"  Classification: {solution1.ode_solution.classification}")
        print(f"  Solver: {solution1.ode_solution.routing_decision.method}")
    
    # Test Case 2: Natural Language PDE
    print("\n" + "="*80)
    print("TEST 2: NATURAL LANGUAGE PDE INPUT (CodePDE-inspired)")
    print("="*80 + "\n")
    
    pde_description = "Solve the 1D heat equation with Dirichlet boundary conditions"
    solution2 = solver.solve_from_natural_language(
        description=pde_description
    )
    
    print("\n📊 RESULTS:")
    print(f"  Mode: {solution2.processing_mode}")
    print(f"  Used LLM: {solution2.used_llm}")
    if solution2.pde_spec:
        print(f"  PDE Type: {solution2.pde_spec.equation_type}")
        print(f"  Equation: {solution2.pde_spec.equation}")
        print(f"  Domain: {solution2.pde_spec.domain}")
        if solution2.generated_solver_code:
            lines = len(solution2.generated_solver_code.split('\n'))
            print(f"  Generated Code: {lines} lines")
    
    # Test Case 3: Enhanced Explanation
    print("\n" + "="*80)
    print("TEST 3: EQUATION WITH LLM-ENHANCED EXPLANATION")
    print("="*80 + "\n")
    
    solution3 = solver.solve_with_explanation(
        equation="x'' + 0.2*x' + x + 0.1*x**3 = cos(t)",
        initial_conditions={'x': 1, 'dx': 0},
        time_span=(0, 50)
    )
    
    print("\n📊 RESULTS:")
    if solution3.ode_solution:
        print(f"  Classification: {solution3.ode_solution.classification}")
        if solution3.used_llm:
            print(f"\n  LLM Explanation (first 300 chars):")
            print("  " + "-"*76)
            print(f"  {solution3.natural_language_explanation[:300]}...")
    
    print("\n" + "🎓 "*40)
    print("DEMONSTRATION COMPLETE")
    print("🎓 "*40 + "\n")
    
    print("\n📝 CAPSTONE PROJECT FEATURES DEMONSTRATED:")
    print("  ✅ Natural language input parsing")
    print("  ✅ Automatic ODE/PDE classification")
    print("  ✅ DeepSeek LLM integration")
    print("  ✅ CodePDE-inspired solver generation")
    print("  ✅ Enhanced explanations")
    print("  ✅ Zero hallucination numerical solving")
    print("  ✅ Production-ready architecture")
    print()


if __name__ == '__main__':
    demo_capstone_features()