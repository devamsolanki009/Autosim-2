from core.parser import ODEParser
from solvers.euler import EulerSolver

parser = ODEParser()
solver = EulerSolver()

eq = "x'' + 0.2*x' + x = cos(t)"
ic = {'x': 1.0, 'dx': 0.0}
components = parser.parse(eq, ic)

sol = solver.solve(components, ic, time_span=(0, 50), variant='forward')
print("Forward Euler success:", sol.success)
print("Steps count:", len(sol.steps_table))
if sol.steps_table:
    print("First step keys:", list(sol.steps_table[0].keys()))
    print("First step:", sol.steps_table[0])
print()

sol2 = solver.solve(components, ic, time_span=(0, 50), variant='improved')
print("Improved Euler success:", sol2.success)
print("Steps count:", len(sol2.steps_table))
if sol2.steps_table:
    print("First step keys:", list(sol2.steps_table[0].keys()))
    print("First step:", sol2.steps_table[0])
