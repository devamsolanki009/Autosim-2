"""
Visualization Module
Professional plots for ODE solutions
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Optional, Dict, List, Tuple
from solvers.numerical import NumericalSolution
import sympy as sp


class ODEVisualizer:
    """Create publication-quality visualizations"""
    
    def __init__(self, style: str = 'seaborn-v0_8-darkgrid'):
        try:
            plt.style.use(style)
        except:
            plt.style.use('default')
        
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'tertiary': '#F18F01',
            'quaternary': '#C73E1D',
            'grid': '#E8E8E8'
        }
    
    def plot_numerical_solution(self,
                               solution: NumericalSolution,
                               equation_str: str,
                               title: Optional[str] = None) -> Figure:
        """
        Plot numerical solution
        
        Creates:
        - Time series of x(t)
        - Phase portrait (if velocity available)
        - Optional: velocity time series
        """
        
        if not solution.success:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"Solution failed: {solution.message}",
                   ha='center', va='center', fontsize=14, color='red')
            ax.axis('off')
            return fig
        
        # Determine layout
        has_velocity = solution.y.shape[0] > 1
        
        if has_velocity:
            fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        else:
            fig, axes = plt.subplots(1, 1, figsize=(10, 6))
            axes = [axes]
        
        t = solution.t
        x = solution.y[0]
        
        # Plot 1: x(t)
        axes[0].plot(t, x, color=self.colors['primary'], linewidth=2, label='x(t)')
        axes[0].set_xlabel('Time (t)', fontsize=12)
        axes[0].set_ylabel('x(t)', fontsize=12)
        axes[0].set_title('Position vs Time', fontsize=14, fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()
        
        if has_velocity:
            v = solution.y[1]
            
            # Plot 2: v(t)
            axes[1].plot(t, v, color=self.colors['secondary'], linewidth=2, label="x'(t)")
            axes[1].set_xlabel('Time (t)', fontsize=12)
            axes[1].set_ylabel("x'(t)", fontsize=12)
            axes[1].set_title('Velocity vs Time', fontsize=14, fontweight='bold')
            axes[1].grid(True, alpha=0.3)
            axes[1].legend()
            
            # Plot 3: Phase portrait
            axes[2].plot(x, v, color=self.colors['tertiary'], linewidth=1.5, alpha=0.8)
            axes[2].scatter([x[0]], [v[0]], color='green', s=100, zorder=5, 
                          label='Start', marker='o')
            axes[2].scatter([x[-1]], [v[-1]], color='red', s=100, zorder=5,
                          label='End', marker='s')
            axes[2].set_xlabel('x(t)', fontsize=12)
            axes[2].set_ylabel("x'(t)", fontsize=12)
            axes[2].set_title('Phase Portrait', fontsize=14, fontweight='bold')
            axes[2].grid(True, alpha=0.3)
            axes[2].legend()
        
        # Overall title
        if title:
            fig.suptitle(title, fontsize=16, fontweight='bold', y=1.02)
        else:
            fig.suptitle(f'ODE Solution: {equation_str}', 
                        fontsize=16, fontweight='bold', y=1.02)
        
        plt.tight_layout()
        return fig
    
    def plot_symbolic_solution(self,
                              solution_expr: sp.Expr,
                              equation_str: str,
                              time_range: Tuple[float, float] = (0, 10),
                              title: Optional[str] = None) -> Figure:
        """Plot symbolic solution"""
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Evaluate symbolic solution
        t_sym = sp.Symbol('t', real=True)
        t_vals = np.linspace(time_range[0], time_range[1], 1000)
        
        try:
            # Convert to numerical function
            func = sp.lambdify(t_sym, solution_expr, 'numpy')
            y_vals = func(t_vals)
            
            ax.plot(t_vals, y_vals, color=self.colors['primary'], linewidth=2.5)
            ax.set_xlabel('Time (t)', fontsize=12)
            ax.set_ylabel('x(t)', fontsize=12)
            ax.grid(True, alpha=0.3)
            
            if title:
                ax.set_title(title, fontsize=14, fontweight='bold')
            else:
                ax.set_title(f'Symbolic Solution: {equation_str}', 
                           fontsize=14, fontweight='bold')
        
        except Exception as e:
            ax.text(0.5, 0.5, f"Could not evaluate symbolic solution:\n{str(e)}",
                   ha='center', va='center', fontsize=12, color='red')
            ax.axis('off')
        
        plt.tight_layout()
        return fig
    
    def plot_comparison(self,
                       solutions: Dict[str, NumericalSolution],
                       equation_str: str,
                       title: str = "Solution Comparison") -> Figure:
        """Compare multiple solutions"""
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        colors = [self.colors['primary'], self.colors['secondary'], 
                 self.colors['tertiary'], self.colors['quaternary']]
        
        for idx, (label, solution) in enumerate(solutions.items()):
            if not solution.success:
                continue
            
            color = colors[idx % len(colors)]
            t = solution.t
            x = solution.y[0]
            
            # Time series
            axes[0].plot(t, x, color=color, linewidth=2, label=label, alpha=0.8)
            
            # Phase portrait (if available)
            if solution.y.shape[0] > 1:
                v = solution.y[1]
                axes[1].plot(x, v, color=color, linewidth=1.5, label=label, alpha=0.8)
        
        axes[0].set_xlabel('Time (t)', fontsize=12)
        axes[0].set_ylabel('x(t)', fontsize=12)
        axes[0].set_title('Position vs Time', fontsize=14, fontweight='bold')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        axes[1].set_xlabel('x(t)', fontsize=12)
        axes[1].set_ylabel("x'(t)", fontsize=12)
        axes[1].set_title('Phase Portrait', fontsize=14, fontweight='bold')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        fig.suptitle(title, fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        return fig
    
    def create_analysis_dashboard(self,
                                 solution: NumericalSolution,
                                 equation_str: str,
                                 components_info: Dict) -> Figure:
        """
        Create comprehensive analysis dashboard
        
        Includes:
        - Solution plot
        - Phase portrait
        - Statistics panel
        - Equation info panel
        """
        
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        t = solution.t
        x = solution.y[0]
        
        # Main plot: x(t)
        ax1 = fig.add_subplot(gs[0:2, 0:2])
        ax1.plot(t, x, color=self.colors['primary'], linewidth=2.5)
        ax1.set_xlabel('Time (t)', fontsize=12)
        ax1.set_ylabel('x(t)', fontsize=12)
        ax1.set_title('Solution: x(t)', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        
        # Phase portrait
        if solution.y.shape[0] > 1:
            v = solution.y[1]
            ax2 = fig.add_subplot(gs[0:2, 2])
            ax2.plot(x, v, color=self.colors['tertiary'], linewidth=2, alpha=0.8)
            ax2.scatter([x[0]], [v[0]], color='green', s=100, zorder=5, marker='o')
            ax2.scatter([x[-1]], [v[-1]], color='red', s=100, zorder=5, marker='s')
            ax2.set_xlabel('x(t)', fontsize=12)
            ax2.set_ylabel("x'(t)", fontsize=12)
            ax2.set_title('Phase Portrait', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
        
        # Statistics panel
        ax3 = fig.add_subplot(gs[2, 0])
        ax3.axis('off')
        
        stats_text = "Statistics\n" + "="*30 + "\n"
        for key, value in solution.statistics.items():
            stats_text += f"{key}: {value:.4f}\n"
        
        ax3.text(0.05, 0.95, stats_text, 
                transform=ax3.transAxes,
                fontsize=10,
                verticalalignment='top',
                fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
        
        # Equation info panel
        ax4 = fig.add_subplot(gs[2, 1:])
        ax4.axis('off')
        
        info_text = "Equation Information\n" + "="*30 + "\n"
        info_text += f"Equation: {equation_str}\n"
        for key, value in components_info.items():
            info_text += f"{key}: {value}\n"
        
        ax4.text(0.05, 0.95, info_text,
                transform=ax4.transAxes,
                fontsize=10,
                verticalalignment='top',
                fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
        
        fig.suptitle('ODE Analysis Dashboard', fontsize=18, fontweight='bold')
        
        return fig


def demo():
    """Demonstrate visualization"""
    from core.parser import ODEParser
    from solvers.numerical import NumericalSolver
    
    parser = ODEParser()
    solver = NumericalSolver()
    viz = ODEVisualizer()
    
    # Solve example
    eq = "x'' + 0.2*x' + x = cos(t)"
    ic = {'x': 1, 'dx': 0}
    
    components = parser.parse(eq)
    solution = solver.solve(components, ic)
    
    if solution.success:
        fig = viz.plot_numerical_solution(solution, eq)
        plt.savefig('/home/claude/ode_viz_demo.png', dpi=150, bbox_inches='tight')
        print("Visualization saved to ode_viz_demo.png")
    else:
        print(f"Solution failed: {solution.message}")


if __name__ == '__main__':
    demo()