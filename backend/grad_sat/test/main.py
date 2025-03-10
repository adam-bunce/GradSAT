from ortools.sat.python import cp_model

# what users are doing is debugging their own constraints (100% in the schedule generation step, ~50% kinda in the verification model)

# okay im missing the "FilterConstraint(100, CSCI)", but how many CSCI do i have? how many more do i need?
# if i know one constraint wasn't met, how can i extract more information
def main():
    model = cp_model.CpModel()

    x = model.new_int_var(0, 5, "x")
    y = model.new_int_var(0, 5, "y")
    z = model.new_int_var(5, 10, "z")

    v1 = model.new_bool_var("x + y >= 11")
    v2 = model.new_bool_var("x + y <= 5")
    v3 = model.new_bool_var("z <= 5")

    model.add(x + y >= 11).only_enforce_if(v1)
    model.add(x + y <= 5).only_enforce_if(v2)
    model.add(z <= 5).only_enforce_if(v3)

    # define assumption literals
    model.add_assumptions([v1, v2, v3])

    # create a solver and solve the model
    solver = cp_model.CpSolver()
    status = solver.solve(model)
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print("Solved")
        print(f"x:{solver.value(x)} | y:{solver.value(y)}")
    else:
        print("Model Unsolvable due to:")
        for var_index in solver.ResponseProto().sufficient_assumptions_for_infeasibility:
            print(model.var_index_to_var_proto(var_index))

def main2():
    # trad map domain, unable to conditionally enforce
    model = cp_model.CpModel()

    x = model.new_bool_var("x")
    y = model.new_bool_var("y")
    z = model.new_bool_var("z")

    model.add(y == 1)
    # model.add(x == 1) this will cause infeasibility

    arr = [x, y, z]
    index = model.new_int_var(0, 100, name="out")
    model.add_map_domain(index, arr, offset=1)

    solver = cp_model.CpSolver()
    status = solver.solve(model)
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print("Solved")
        print("index", solver.value(index))
        for val in arr:
            print(val.name, solver.value(val))
    else:
        print("Model Unsolvable")

def main2():
    model = cp_model.CpModel()

    x = model.new_bool_var("x")
    y = model.new_bool_var("y")
    z = model.new_bool_var("z")

    model.add(y == 1)
    # model.add(x == 1) this will cause infeasibility

    arr = [x, y, z]
    index = model.new_int_var(0, 100, name="out")
    model.add_map_domain(index, arr, offset=1)

    solver = cp_model.CpSolver()
    status = solver.solve(model)
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print("Solved")
        print("index", solver.value(index))
        for val in arr:
            print(val.name, solver.value(val))
    else:
        print("Model Unsolvable")


if __name__ == "__main__":
    main2()
