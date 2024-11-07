from ortools.sat.python import cp_model
import pandas as pd


def are_all_true(
    model: cp_model.CpModel, variables: list[cp_model.BoolVarT]
) -> cp_model.BoolVarT:
    all_vars_true = model.new_bool_var(f"{'∧'.join([str(var) for var in variables])}")
    model.add_bool_and(variables).only_enforce_if(all_vars_true)
    model.add_bool_or([~var for var in variables]).only_enforce_if(~all_vars_true)

    return all_vars_true


def false_var(model: cp_model.CpModel) -> cp_model.BoolVarT:
    var = model.new_bool_var("false_var")
    model.add(var == 0)
    return var


class AllTakenDict(dict):
    def __init__(self, model: cp_model.CpModel, taken: pd.Series):
        super().__init__()
        self.model = model
        self.taken = taken

    def __missing__(self, key):
        assert len(key) > 1, "Expected multiple courses"

        try:
            taken_vars = [self.taken[course_name] for course_name in key]
        except KeyError:
            # one of the courses doesn't exist, so they can't all be taken
            var = false_var(self.model)
            self[key] = var
            return var

        all_taken = are_all_true(self.model, taken_vars)

        self[key] = all_taken
        return all_taken


class TakenBeforeDict(dict):
    def __init__(
        self,
        model: cp_model.CpModel,
        taken_in: pd.Series,
        taken: pd.Series,
        all_taken: AllTakenDict,
    ):
        super().__init__()
        self.model = model
        self.taken_in = taken_in
        self.taken = taken
        self.all_taken = all_taken

    def __missing__(self, key):
        assert len(key) == 2, "Key must contain exactly two values."
        class_1, class_2 = key

        class_1_taken_before_class_2 = self.model.new_bool_var(
            f"{class_1}_taken_before_{class_2}?"
        )

        if class_1 not in self.taken.index or class_2 not in self.taken.index:
            self.model.add(class_1_taken_before_class_2 == 0)
            self[key] = class_1_taken_before_class_2
            return class_1_taken_before_class_2

        # can only be 'taken before' if both courses are taken
        class_1_and_class_2_taken = self.all_taken[(class_1, class_2)]
        self.model.add(class_1_and_class_2_taken == 1).only_enforce_if(
            class_1_taken_before_class_2
        )

        # class_1 must be taken_in year lower than class_2, if we take class_2
        self.model.add(self.taken_in[class_1] < self.taken_in[class_2]).only_enforce_if(
            self.taken[class_2]
        )

        self[key] = class_1_taken_before_class_2
        return class_1_taken_before_class_2
