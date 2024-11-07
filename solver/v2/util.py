from ortools.sat.python import cp_model


def print_statistics(solver: cp_model.CpSolver) -> None:
    print("\nStatistics")
    print(f"  - conflicts      : {solver.num_conflicts}")
    print(f"  - branches       : {solver.num_branches}")
    print(f"  - wall time      : {solver.wall_time} s")
