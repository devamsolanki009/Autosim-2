"""
Numerical ODE Solver
Handles nonlinear, stiff, and complex systems
"""

import numpy as np
from scipy.integrate import solve_ivp
from typing import Dict, List, Tuple, Callable
from dataclasses import dataclass
from core.parser import ODEComponents, ODEParser


@dataclass
class NumericalSolution:
    """Complete numerical solution"""
    t: np.ndarray
    y: np.ndarray  # Shape: (n_states, n_timepoints)
    success: bool
    message: str
    method: str
    statistics: Dict[str, float]


class NumericalSolver:
    """Solve ODEs numerically"""
    
    def __init__(self):
        self.parser = ODEParser()
    
    def solve(self, 
              components: ODEComponents,
              initial_conditions: Dict[str, float],
              time_span: Tuple[float, float] = (0, 50),
              method: str = 'RK45',
              dense_output: bool = True) -> NumericalSolution:
        """
        Solve ODE numerically
        
        Args:
            components: Parsed ODE components
            initial_conditions: {'x': x0, 'dx': dx0, ...}
            time_span: (t_start, t_end)
            method: 'RK45', 'Radau', 'BDF', 'LSODA', etc.
            dense_output: Whether to generate dense output
        
        Returns:
            NumericalSolution with time series and statistics
        """
        
        # Convert to first-order system
        system_func, y0 = self.parser.to_first_order_system(components, initial_conditions)
        
        # Solve
        t_span = time_span
        t_eval = np.linspace(t_span[0], t_span[1], 1000)
        
        try:
            sol = solve_ivp(
                system_func,
                t_span,
                y0,
                method=method,
                t_eval=t_eval,
                dense_output=dense_output,
                rtol=1e-8,
                atol=1e-10
            )
            
            # Compute statistics
            stats = self._compute_statistics(sol.t, sol.y)
            
            return NumericalSolution(
                t=sol.t,
                y=sol.y,
                success=sol.success,
                message=sol.message,
                method=method,
                statistics=stats
            )
        
        except Exception as e:
            # Failed - return empty solution
            return NumericalSolution(
                t=np.array([]),
                y=np.array([[]]),
                success=False,
                message=str(e),
                method=method,
                statistics={}
            )
    
    def _compute_statistics(self, t: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Compute solution statistics"""
        
        # y shape: (n_states, n_timepoints)
        x = y[0]  # First state (position)
        
        stats = {
            'x_final': float(x[-1]),
            'x_max': float(np.max(x)),
            'x_min': float(np.min(x)),
            'x_mean': float(np.mean(x)),
            'x_std': float(np.std(x)),
        }
        
        # If velocity available
        if y.shape[0] > 1:
            v = y[1]
            stats.update({
                'v_final': float(v[-1]),
                'v_max': float(np.max(v)),
                'v_min': float(np.min(v)),
            })
        
        # Period estimation (if oscillatory)
        try:
            from scipy.signal import find_peaks
            peaks, _ = find_peaks(x)
            if len(peaks) > 1:
                periods = np.diff(t[peaks])
                stats['period_estimate'] = float(np.mean(periods))
                stats['frequency_estimate'] = float(1.0 / stats['period_estimate'])
        except:
            pass
        
        return stats
    
    def solve_system(self,
                     system_func: Callable,
                     y0: List[float],
                     time_span: Tuple[float, float] = (0, 50),
                     method: str = 'RK45') -> NumericalSolution:
        """
        Solve a system of ODEs directly
        
        Args:
            system_func: Function with signature f(t, y) -> dy/dt
            y0: Initial state vector
            time_span: Time interval
            method: Integration method
        """
        
        t_span = time_span
        t_eval = np.linspace(t_span[0], t_span[1], 1000)
        
        sol = solve_ivp(
            system_func,
            t_span,
            y0,
            method=method,
            t_eval=t_eval,
            rtol=1e-8,
            atol=1e-10
        )
        
        stats = self._compute_statistics(sol.t, sol.y)
        
        return NumericalSolution(
            t=sol.t,
            y=sol.y,
            success=sol.success,
            message=sol.message,
            method=method,
            statistics=stats
        )


def demo():
    """Demonstrate numerical solver"""
    from core.parser import ODEParser
    from core.router import ODERouter
    
    parser = ODEParser()
    router = ODERouter()
    solver = NumericalSolver()
    
    # Test: Duffing oscillator
    eq = "x'' + 0.2*x' + x + 0.1*x**3 = cos(t)"
    ic = {'x': 1, 'dx': 0}
    
    print(f"Solving: {eq}")
    print(f"Initial conditions: {ic}")
    print()
    
    components = parser.parse(eq)
    decision = router.route(components)
    
    print(f"Solver: {decision.solver_type} ({decision.method})")
    print(f"Reason: {decision.reason}")
    print()
    
    if decision.solver_type == 'numerical':
        solution = solver.solve(components, ic, method=decision.method)
        
        if solution.success:
            print("Solution computed successfully!")
            print("\nStatistics:")
            for key, value in solution.statistics.items():
                print(f"  {key}: {value:.4f}")
            
            print(f"\nTime points: {len(solution.t)}")
            print(f"Final state: x = {solution.y[0][-1]:.4f}, v = {solution.y[1][-1]:.4f}")
        else:
            print(f"Failed: {solution.message}")


if __name__ == '__main__':
    demo()