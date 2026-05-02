"""
Robust ODE Equation Parser
Extracts order, terms, coefficients, and converts to computational form
"""

import re
import sympy as sp
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ODEComponents:
    """Structured representation of parsed ODE"""
    equation: str
    order: int
    is_linear: bool
    is_homogeneous: bool
    coefficients: Dict[str, float]
    nonlinear_terms: List[str]
    forcing_function: Optional[str]
    symbolic_form: sp.Eq
    variables: Dict[str, sp.Symbol]


class ODEParser:
    """Parse ODE equations into structured components"""
    
    def __init__(self):
        self.t = sp.Symbol('t', real=True)
        self.x = sp.Function('x')
        
    def parse(self, equation_str: str, initial_conditions: Dict[str, float] = None) -> ODEComponents:
        """
        Parse ODE string into components
        
        Examples:
            "x'' + 2*x' + x = 0"
            "x'' + 0.2*x' + x + 0.1*x^3 = cos(t)"
            "dx/dt = -0.5*x + 2"
        """
        # Clean equation
        eq = equation_str.replace(' ', '')
        eq = self._normalize_notation(eq)
        
        # Split into LHS and RHS
        if '=' in eq:
            lhs, rhs = eq.split('=', 1)   # split only once
        else:
            lhs, rhs = eq, '0'
        
        # Detect order
        order = self._detect_order(lhs)
        
        # Parse into sympy
        rhs_expr = None
        lhs_expr = None
        try:
            lhs_expr = self._parse_expression(lhs)
            rhs_expr = self._parse_expression(rhs)
            symbolic_eq = sp.Eq(lhs_expr, rhs_expr)
        except Exception as e:
            # Fallback: create equation object anyway
            symbolic_eq = None
        
        # Analyze linearity
        is_linear, nonlinear_terms = self._check_linearity(lhs)
        
        # Extract coefficients
        coefficients = self._extract_coefficients(lhs)
        
        # Check homogeneity
        is_homogeneous = (rhs == '0' or rhs_expr == 0) if rhs_expr is not None else (rhs == '0')
        
        # Forcing function
        forcing = rhs if not is_homogeneous else None
        
        return ODEComponents(
            equation=equation_str,
            order=order,
            is_linear=is_linear,
            is_homogeneous=is_homogeneous,
            coefficients=coefficients,
            nonlinear_terms=nonlinear_terms,
            forcing_function=forcing,
            symbolic_form=symbolic_eq,
            variables={'t': self.t, 'x': self.x(self.t)}
        )
    
    def _normalize_notation(self, eq: str) -> str:
        """Convert various notations to standard form"""
        # Convert dx/dt to x'
        eq = re.sub(r'd(\d*)x/dt(\d*)', lambda m: f"x{self._prime_notation(m.group(1) or '1')}", eq)
        
        # Convert x^n to x**n
        eq = eq.replace('^', '**')
        
        # Ensure multiplication is explicit for digits followed by letters
        eq = re.sub(r'(\d)([a-z])', r'\1*\2', eq)
        # Insert * between a single letter and ( only — not after known math functions.
        # Match a letter that is NOT preceded by another letter (i.e. it's a standalone
        # variable like x or t, not the tail of sin/cos/exp/tan/log/sqrt/abs).
        eq = re.sub(r'(?<![a-z])([a-z])(\()', r'\1*\2', eq)
        
        return eq
    
    def _prime_notation(self, order_str: str) -> str:
        """Convert order number to prime notation"""
        order = int(order_str)
        return "'" * order
    
    def _detect_order(self, expr: str) -> int: 
        """Detect highest derivative order"""
        # Count maximum number of primes
        max_primes = 0
        
        # Check for x', x'', x''', etc.
        matches = re.findall(r"x'*", expr)
        for match in matches:
            prime_count = match.count("'")
            max_primes = max(max_primes, prime_count)
        
        # Check for derivative notation
        if 'd2x' in expr or 'd²x' in expr:
            max_primes = max(max_primes, 2)
        if 'd3x' in expr or 'd³x' in expr:
            max_primes = max(max_primes, 3)
        
        return max(max_primes, 1)  # At least first order
    
    def _parse_expression(self, expr_str: str) -> sp.Expr:
        """Convert string to sympy expression"""
        # Replace derivatives with symbols for parsing
        expr = expr_str
        
        # x''' -> d3x, x'' -> d2x, x' -> dx
        expr = re.sub(r"x'''", 'dx3', expr)
        expr = re.sub(r"x''", 'dx2', expr)
        expr = re.sub(r"x'", 'dx1', expr)
        expr = re.sub(r"(?<!')x(?!')", 'x0', expr)  # x -> x0 (but not x')
        
        # Create symbols
        x0 = sp.Symbol('x0', real=True)
        dx1 = sp.Symbol('dx1', real=True)
        dx2 = sp.Symbol('dx2', real=True)
        dx3 = sp.Symbol('dx3', real=True)
        t = sp.Symbol('t', real=True)
        
        # Parse
        parsed = sp.sympify(expr, locals={'x0': x0, 'dx1': dx1, 'dx2': dx2, 'dx3': dx3, 't': t})
        
        return parsed
    
    def _check_linearity(self, expr: str) -> Tuple[bool, List[str]]:
        """Check if ODE is linear and find nonlinear terms"""
        nonlinear_patterns = [
            r'x\*\*\d+',  # x**2, x**3
            r'x\*x',       # x*x
            r'sin\(x\)',   # sin(x)
            r'cos\(x\)',   # cos(x)
            r'exp\(x\)',   # exp(x)
            r'log\(x\)',   # log(x)
            r'abs\(x\)',   # abs(x)
        ]
        
        nonlinear_terms = []
        for pattern in nonlinear_patterns:
            matches = re.findall(pattern, expr)
            if matches:
                nonlinear_terms.extend(matches)
        
        is_linear = len(nonlinear_terms) == 0
        
        return is_linear, nonlinear_terms
    
    def _extract_coefficients(self, expr: str) -> Dict[str, float]:
        """Extract coefficients of derivatives and linear x term only"""
        coeffs = {}
        
        # Pattern: number before x''', x'', x' (derivatives only)
        # For x (non-derivative), we need to be more careful
        patterns = [
            (r'([+-]?\d*\.?\d+)\*?x\'\'\'', 'x3'),
            (r'([+-]?\d*\.?\d+)\*?x\'\'', 'x2'),
            (r'([+-]?\d*\.?\d+)\*?x\'', 'x1'),
        ]
        
        # Extract derivative coefficients first
        for pattern, name in patterns:
            match = re.search(pattern, expr)
            if match:
                coeff_str = match.group(1)
                if coeff_str in ['', '+']:
                    coeffs[name] = 1.0
                elif coeff_str == '-':
                    coeffs[name] = -1.0
                else:
                    coeffs[name] = float(coeff_str)
        
        # Also check for just x''', x'', x' without explicit coefficient (implicit 1)
        if "x'''" in expr and 'x3' not in coeffs:
            match = re.search(r'([+-]?)x\'\'\'', expr)
            if match:
                sign = match.group(1)
                coeffs['x3'] = 1.0 if sign != '-' else -1.0
        
        if "x''" in expr and 'x2' not in coeffs:
            match = re.search(r'([+-]?)x\'\'', expr)
            if match:
                sign = match.group(1)
                coeffs['x2'] = 1.0 if sign != '-' else -1.0
        
        if "x'" in expr and 'x1' not in coeffs:
            # Make sure not x'' or x'''
            matches = re.findall(r'([+-]?)x\'(?!\')', expr)
            if matches:
                sign = matches[0]
                coeffs['x1'] = 1.0 if sign != '-' else -1.0
        
        # For x (non-derivative), we need to extract ONLY the linear term coefficient
        # NOT from x**2, x**3, etc.
        # Pattern: number*x where x is NOT followed by *, ', or **
        if 'x0' not in coeffs:
            # Look for patterns like "+x", "-x", "+2*x", "3*x" where x is standalone
            # But NOT "0.1*x**3"
            pattern = r'([+-]?\d*\.?\d*)\*?x(?![\'\*])'
            matches = re.findall(pattern, expr)
            
            # Filter out matches that are part of nonlinear terms
            # Check context: if followed by ** it's nonlinear
            linear_matches = []
            for i, match in enumerate(matches):
                # Find position of this match in string
                idx = 0
                for _ in range(i + 1):
                    idx = expr.find('x', idx) + 1
                # Check if followed by **
                if idx < len(expr) and expr[idx:idx+2] != '**':
                    linear_matches.append(match)
            
            if linear_matches:
                coeff_str = linear_matches[0]
                if coeff_str in ['', '+']:
                    coeffs['x0'] = 1.0
                elif coeff_str == '-':
                    coeffs['x0'] = -1.0
                elif coeff_str:
                    coeffs['x0'] = float(coeff_str)
                else:
                    # Just standalone 'x'
                    coeffs['x0'] = 1.0
        
        return coeffs
    
    def to_first_order_system(self, components: ODEComponents, 
                              initial_conditions: Dict[str, float]) -> Tuple[callable, List[float]]:
        """
        Convert higher-order ODE to first-order system
        
        For x'' + a*x' + b*x = f(t):
        Let y1 = x, y2 = x'
        Then: y1' = y2
              y2' = f(t) - a*y2 - b*y1
        """
        if components.order == 1:
            # Already first order
            def system(t, y):
                # Parse and evaluate
                # This is simplified - in production, use sympify
                return [eval(components.equation.replace('x', 'y[0]').replace('t', 'str(t)'))]
            
            y0 = [initial_conditions.get('x', 0)]
            return system, y0
        
        elif components.order == 2:
            # Convert to system
            def system(t, y):
                """
                y[0] = x
                y[1] = x'
                Returns [x', x'']
                """
                x, x_dot = y
                
                # Build x'' from equation
                # x'' = RHS - coeffs['x1']*x' - coeffs['x0']*x - nonlinear_terms
                
                # Parse RHS
                if components.forcing_function:
                    forcing = self._evaluate_forcing(components.forcing_function, t)
                else:
                    forcing = 0
                
                # Linear terms
                a = components.coefficients.get('x1', 0)  # Coefficient of x'
                b = components.coefficients.get('x0', 0)  # Coefficient of x
                
                # Nonlinear terms (simplified evaluation)
                nonlinear = self._evaluate_nonlinear(components.nonlinear_terms, x, x_dot)
                
                x_ddot = forcing - a * x_dot - b * x - nonlinear
                
                return [x_dot, x_ddot]
            
            y0 = [
                initial_conditions.get('x', 0),
                initial_conditions.get('dx', 0)
            ]
            
            return system, y0
        
        else:
            raise NotImplementedError(f"Order {components.order} not yet supported")
    
    def _evaluate_forcing(self, forcing_str: str, t: float) -> float:
        """Evaluate forcing function at time t"""
        import numpy as np
        
        # Simple replacement-based evaluation
        # Replace common functions
        expr = forcing_str.lower()
        expr = expr.replace('cos(t)', f'np.cos({t})')
        expr = expr.replace('sin(t)', f'np.sin({t})')
        expr = expr.replace('exp(t)', f'np.exp({t})')
        expr = expr.replace('t', str(t))
        
        try:
            return float(eval(expr, {'np': np}))
        except:
            # If that fails, return 0
            return 0.0
    
    def _evaluate_nonlinear(self, terms: List[str], x: float, x_dot: float) -> float:
        """Evaluate nonlinear terms"""
        import numpy as np
        result = 0
        
        for term in terms:
            try:
                # Extract coefficient if present
                # e.g., "0.1*x**3" or "x**3"
                if '*x' in term:
                    parts = term.split('*x')
                    coeff = float(parts[0]) if parts[0] and parts[0] not in ['+', '-'] else (1.0 if parts[0] != '-' else -1.0)
                    remaining = 'x' + parts[1]
                else:
                    coeff = 1.0
                    remaining = term
                
                # Evaluate the term
                if '**' in remaining:
                    # x**n
                    power = int(remaining.split('**')[1])
                    value = coeff * (x ** power)
                elif 'x*x' in remaining:
                    value = coeff * (x * x)
                elif 'sin(x)' in remaining:
                    value = coeff * np.sin(x)
                elif 'cos(x)' in remaining:
                    value = coeff * np.cos(x)
                elif 'exp(x)' in remaining:
                    value = coeff * np.exp(x)
                else:
                    value = 0
                
                result += value
            except Exception as e:
                # Skip malformed terms
                pass
        
        return result


def demo():
    """Demonstration of parser capabilities"""
    parser = ODEParser()
    
    test_cases = [
        "x'' + x = 0",
        "x'' + 2*x' + x = 0",
        "x'' + 0.2*x' + x + 0.1*x**3 = cos(t)",
        "dx/dt = -0.5*x + 2",
    ]
    
    for eq in test_cases:
        print(f"\n{'='*60}")
        print(f"Equation: {eq}")
        print('='*60)
        
        components = parser.parse(eq)
        
        print(f"Order: {components.order}")
        print(f"Linear: {components.is_linear}")
        print(f"Homogeneous: {components.is_homogeneous}")
        print(f"Coefficients: {components.coefficients}")
        print(f"Nonlinear terms: {components.nonlinear_terms}")
        print(f"Forcing: {components.forcing_function}")


if __name__ == '__main__':
    demo()