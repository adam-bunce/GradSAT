from ortools.sat.python import cp_model
import pandas as pd

from solver.v2.static import int_to_semester


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


def zero_int(model: cp_model.CpModel) -> cp_model.IntVar:
    var = model.new_int_var(0, 0, "empty_int")
    return var


def empty_interval(
    model: cp_model.CpModel, is_present: cp_model.BoolVarT
) -> cp_model.IntervalVar:
    return model.new_optional_interval_var(
        start=model.new_int_var(lb=0, ub=0, name="empty_interval_start"),
        end=model.new_int_var(lb=0, ub=0, name="empty_interval_end"),
        size=model.new_int_var(lb=0, ub=0, name="empty_interval_size"),
        is_present=is_present,
        name="empty_interval",
    )


class AllTakenDict(dict):
    def __init__(self, model: cp_model.CpModel, taken: pd.Series):
        super().__init__()
        self.model = model
        self.taken = taken

    def __missing__(self, key: str):
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
            # gonna get standing in here
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


class TakenBeforeOrConcurrentlyDict(dict):
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
            f"{class_1}_taken_before_or_concurrently_with_{class_2}?"
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

        # class_1 must be taken_in year lower than class_2 or in the same year, if we take class_2
        self.model.add(
            self.taken_in[class_1] <= self.taken_in[class_2]
        ).only_enforce_if(self.taken[class_2])

        self[key] = class_1_taken_before_class_2
        return class_1_taken_before_class_2


class TakenAfterDict(dict):
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
        print(class_1, class_2)

        class_1_taken_before_class_2 = self.model.new_bool_var(
            f"{class_1}_taken_after_{class_2}?"
        )

        print(class_1_taken_before_class_2)

        if class_1 not in self.taken.index or class_2 not in self.taken.index:
            self.model.add(class_1_taken_before_class_2 == 0)
            self[key] = class_1_taken_before_class_2
            return class_1_taken_before_class_2

        # can only be 'taken before' if both courses are taken
        class_1_and_class_2_taken = self.all_taken[(class_1, class_2)]
        self.model.add(class_1_and_class_2_taken == 1).only_enforce_if(
            class_1_taken_before_class_2
        )

        # class_1 must be taken_in year greater than class_2, if we take class_2
        self.model.add(self.taken_in[class_1] > self.taken_in[class_2]).only_enforce_if(
            self.taken[class_2]
        )

        self[key] = class_1_taken_before_class_2
        return class_1_taken_before_class_2


class StandingPrerequisiteDict(dict):
    def __init__(self, model: cp_model.CpModel, taken: pd.Series, taken_in: pd.Series):
        super().__init__()
        self.model = model
        self.taken = taken
        self.taken_in = taken_in

    def __missing__(self, key):
        standing_prereq, course = key

        min_semester = 0
        if standing_prereq == "first_year_standing":
            min_semester = 1
        elif standing_prereq == "second_year_standing":
            min_semester = 3
        elif standing_prereq == "third_year_standing":
            min_semester = 5
        elif standing_prereq == "fourth_year_standing":
            min_semester = 7

        course_taken_in = self.taken_in[course]

        met_pre_req = self.model.new_bool_var(
            f"{standing_prereq}_or_greater_when_taking_{course}?"
        )

        # if we had met the year threshold to take the course, then we met the prerequisite, otherwise we didn't
        self.model.add(course_taken_in >= min_semester).only_enforce_if(met_pre_req)
        self.model.add(course_taken_in < min_semester).only_enforce_if(~met_pre_req)

        return met_pre_req


class CreditHoursPerSemesterDict(dict):
    def __init__(
        self,
        model: cp_model.CpModel,
        courses: pd.DataFrame,
        course_credit_hours: pd.Series,
    ):
        super().__init__()
        self.model = model
        self.courses = courses
        self.course_credit_hours = course_credit_hours

        previous_semester_str_ids = []
        for semester_id, semester_str_id in int_to_semester.items():
            if semester_id == 1:
                # no credits in first sem
                self[semester_id] = false_var(self.model)
                previous_semester_str_ids.append(semester_str_id)
                continue

            # really high upper bound because we scale it to get rid of decimals
            var = self.model.new_int_var(
                lb=0, ub=1_000_000, name=f"credit_hours_at_{semester_str_id}"
            )

            self.model.add(
                var
                == sum(
                    [
                        sum(row[:-1]) * (int(row[-1] * 10))
                        for row in self.courses.join(self.course_credit_hours)[
                            previous_semester_str_ids + ["credit_hours"]
                        ].itertuples(index=False)
                    ]
                )
            )

            previous_semester_str_ids.append(semester_str_id)
            self[semester_id] = var

    def __missing__(self, key):
        self[key] = 0
        return self[key]


class CreditHourPrerequisiteDict(dict):
    # when we took this course, did we have n credits?
    def __init__(
        self,
        model: cp_model.CpModel,
        taken_in: pd.Series,
        credit_hours_per_semester: dict[str, any],
    ):
        super().__init__()
        self.model = model
        self.taken_in = taken_in
        self.credit_hours_per_semester = credit_hours_per_semester

    def __missing__(self, key):
        credit_hours_prereq, course = key

        met_pre_req = self.model.new_bool_var(f"{course}_meets_{credit_hours_prereq}")
        pos = 0
        while credit_hours_prereq[pos].isnumeric():
            pos += 1
        min_credit_hours = int(credit_hours_prereq[0:pos])

        course_taken_in = self.taken_in[course]

        accumulator = []
        for sem_id_int, sem_id_str in int_to_semester.items():
            var = self.model.new_bool_var(
                f"took_{course}_in_{sem_id_int}_and_{sem_id_int-1}_has_{min_credit_hours}?"
            )

            # it's true if we had enough credits
            self.model.add(
                self.credit_hours_per_semester[sem_id_int - 1] >= min_credit_hours * 10
            ).only_enforce_if(var)

            # and if we took it that semester
            self.model.add(course_taken_in == sem_id_int).only_enforce_if(var)

            accumulator.append(var)

        self.model.add_at_least_one(accumulator).only_enforce_if(met_pre_req)
        self.model.add(sum(accumulator) == 0).only_enforce_if(~met_pre_req)

        self[key] = met_pre_req
        return self[key]
