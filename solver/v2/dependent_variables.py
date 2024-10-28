from ortools.sat.python import cp_model
import pandas as pd


# IDEA: utilities like this whenever i need them kinda like extentions
# or tools for ease of use of repetetive dependent variables
# TODO: use in all_taken
def are_all_true(
    model: cp_model.CpModel, variables: list[cp_model.BoolVarT]
) -> cp_model.BoolVarT:
    all_vars_true = model.new_bool_var(
        f"{''.join([str(var) for var in variables])}_all_true?"
    )

    model.add_bool_and(variables).only_enforce_if(all_vars_true)
    model.add_bool_or([~var for var in variables]).only_enforce_if(~all_vars_true)

    return all_vars_true


class AllTakenDict(dict):
    def __init__(self, model: cp_model.CpModel, taken: pd.Series):
        super().__init__()
        self.model = model
        self.taken = taken

    def __missing__(self, key):
        assert len(key) > 1, "Expected multiple courses"

        all_taken = self.model.new_bool_var(
            f"{''.join([course_name + '_' for course_name in key])}_all_taken?"
        )

        taken_vars = [self.taken[course_name] for course_name in key]

        self.model.add_bool_and(taken_vars).only_enforce_if(all_taken)
        self.model.add_bool_or(
            [~course_taken for course_taken in taken_vars]
        ).only_enforce_if(~all_taken)

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
        print(class_2)

        class_1_taken_before_class_2 = self.model.new_bool_var(
            f"{class_1}_taken_before_{class_2}?"
        )

        # NOTE: issue is that when its 0 its still there and its not lower
        # so i need to only apply some of these is the class is gonna be taken otherwise

        # i think i need to always do .only_enforce_if's here because
        # otherwise we apply these to all courses even if tehyre not used?

        # can only be 'taken before' if both courses are taken
        class_1_and_class_2_taken = self.all_taken[(class_1, class_2)]
        self.model.add(class_1_and_class_2_taken == 1).only_enforce_if(
            self.taken[class_2]
        )

        # class_1 must be taken_in year lower than class_2
        self.model.add(self.taken_in[class_1] < self.taken_in[class_2]).only_enforce_if(
            self.taken[class_2]
        )

        self[key] = class_1_taken_before_class_2
        return class_1_taken_before_class_2
