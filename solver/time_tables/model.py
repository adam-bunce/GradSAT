from collections import defaultdict, namedtuple

import numpy as np
import pandas as pd
from ortools.sat.python import cp_model

from scraper.models import MinimumClassInfo
from solver.v2.dependent_variables import (
    false_var,
    zero_int,
    empty_interval,
    are_all_true,
    create_optional_interval_variable,
    true_var,
)


class TTSolution:
    def __init__(self, courses_taken: list[str], courses: pd.DataFrame, status: any):
        self.courses_taken = courses_taken
        self.courses = courses
        self.status = status

    def __str__(self):
        buf = ""
        if self.status in [
            cp_model.UNKNOWN,
            cp_model.INFEASIBLE,
            cp_model.MODEL_INVALID,
        ]:
            buf += "No Solution"
        else:
            buf += "Solved\n"
            courses_taken_info = defaultdict(list)

            for course_nid in self.courses_taken:
                course_info = self.courses.loc[course_nid]
                for meeting_time in course_info["meeting_times"]:
                    courses_taken_info[meeting_time.day_of_week()].append(
                        (
                            course_nid,
                            meeting_time.begin_time,
                            meeting_time.end_time,
                        )
                    )

            for day_of_week in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
                courses_on_day = courses_taken_info[day_of_week]
                buf += f"{day_of_week}: \n"
                for course in sorted(courses_on_day, key=lambda x: x[1]):
                    buf += f"\t{course[0]:30} ({course[1]} -> {course[2]})"
                    buf += "\n"

        return buf


class TTProblemInstance:
    def __init__(
        self,
        courses: list[MinimumClassInfo],
        forced_conflicts: list[tuple[int, int, str]],
    ):

        self.courses = self.__init_courses(courses)
        self.forced_conflicts: list[tuple[int, int, str]] = forced_conflicts

    @staticmethod
    def __init_courses(courses: list[MinimumClassInfo]):
        index = []
        variables = []
        columns = ["id", "class_code", "type", "meeting_times", "linked_sections"]

        for course in courses:
            variables.append([getattr(course, col) for col in columns])
            index.append(course.info_id())

        return pd.DataFrame(variables, index=index, columns=columns)

    def add_forced_conflict(self, start: int, end: int, day: str):
        assert 0 <= start <= 2359, "start should be between 0 and 2359 (24 hour clock)"
        assert 0 <= end <= 2359, "end should be between 0 and 2359 (24 hour clock)"
        assert day.lower() in [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
        ], "invalid day of the week"

        self.forced_conflicts.append((start, end, day))


class TTDependantVariables:
    def __init__(self, model: cp_model.CpModel, courses: pd.DataFrame):
        self.__courses = courses
        self.__model = model

        self.course_was_taken: dict[str, cp_model.BoolVarT] = (
            self._init_unknown_variables()
        )
        self.intervals: pd.DataFrame = self._init_interval_variables()
        self.intervals.to_html("tmp.html")

    def _init_unknown_variables(self) -> dict[str, cp_model.BoolVarT]:
        course_taken = dict()

        for i, course_info_id in enumerate(self.__courses.index):
            course_taken[course_info_id] = self.__model.new_bool_var(
                f"{course_info_id}_taken?"
            )

        return course_taken

    def _init_interval_variables(self) -> pd.DataFrame:
        new_rows = []
        index = []
        columns = ["start", "end", "interval", "day_of_week"]

        for row_index, row in self.__courses.iterrows():
            if len(row["meeting_times"]) == 0:
                index.append(row_index)

                # start, end, interval (d_vars) day of week (str)
                new_rows.append(
                    [
                        zero_int(self.__model),
                        zero_int(self.__model),
                        empty_interval(
                            self.__model, is_present=false_var(self.__model)
                        ),
                        "NA",
                    ]
                )

            else:
                for j, meeting_time in enumerate(row["meeting_times"]):
                    index.append(row_index)

                    curr_course_was_taken = self.course_was_taken[str(row_index)]
                    start, end, interval = create_optional_interval_variable(
                        model=self.__model,
                        start=meeting_time.begin_time,
                        end=meeting_time.end_time,
                        enforce=curr_course_was_taken,
                        name=str(row_index),
                    )

                    new_rows.append([start, end, interval, meeting_time.day_of_week()])

        return pd.DataFrame(data=new_rows, columns=columns, index=index)


class TTSolver:
    def __init__(self, problem_instance: TTProblemInstance):
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.problem_instance = problem_instance

        self.d_vars = TTDependantVariables(
            model=self.model, courses=problem_instance.courses
        )

        self.forced_conflicts: dict[str, list[cp_model.IntervalVar]] = (
            self.__init_forced_conflicts()
        )

        self._build_model()

    def add_no_overlap_constraint(self):
        # we cant take two classes that are scheduled for the same time
        for day in self.d_vars.intervals["day_of_week"].unique():
            course_intervals = self.d_vars.intervals[
                self.d_vars.intervals["day_of_week"] == day
            ]["interval"].values

            forced_conflict_intervals = np.array(self.forced_conflicts[day])

            all_intervals = np.concatenate(
                (course_intervals, forced_conflict_intervals)
            )

            self.model.add_no_overlap(all_intervals)

    def add_tmp_constraint(self):
        # tmp constraint to ignore courses with no scheduling (sanity checks are easier)
        for course in self.problem_instance.courses.index:
            curr_course_was_taken = self.d_vars.course_was_taken[course]

            if len(self.problem_instance.courses.loc[course]["meeting_times"]) == 0:
                self.model.add(curr_course_was_taken == 0)

    def add_max_of_course_type_constraint(self):
        duplicate_courses: list[list[str]] = list(
            self.problem_instance.courses.groupby(["class_code", "type"]).apply(
                lambda x: x.index.tolist()
            )
        )

        # CONSTRAINT: if a course is taken, the same course shouldn't be taken again
        for courses in duplicate_courses:
            self.model.add(
                sum([self.d_vars.course_was_taken[course] for course in courses]) <= 1
            )

    def __init_forced_conflicts(self) -> dict[str, list[cp_model.IntervalVar]]:
        fc_map = defaultdict(list)
        for start, end, day in self.problem_instance.forced_conflicts:
            _, _, interval_var = create_optional_interval_variable(
                model=self.model,
                start=start,
                end=end,
                enforce=true_var(self.model),
                name=f"forced_conflict_s{start}_e{end}_{day}",
            )

            fc_map[day].append(interval_var)

        return fc_map

    def add_linked_sections_constraint(self):
        # if a course is taken, one of its linked sections (dnf) must be taken as well
        for course_id, row in self.problem_instance.courses.iterrows():
            if len(row["linked_sections"]) != 0:
                course_taken = self.d_vars.course_was_taken[str(course_id)]

                # print("course taken?", course_taken)
                possible_linked_sections = []
                for linked_section in row["linked_sections"]:
                    linked_sections_taken = [
                        self.d_vars.course_was_taken[course_name]
                        for course_name in self.problem_instance.courses.query(
                            "id in @linked_section"
                        ).index.to_list()
                    ]

                    possible_linked_sections.append(
                        are_all_true(self.model, linked_sections_taken)
                    )

                # we're not going to take a lab twice, take it once
                self.model.add(sum(possible_linked_sections) == 1).only_enforce_if(
                    course_taken
                )

    def _add_constraints(self):
        self.add_max_of_course_type_constraint()
        self.add_no_overlap_constraint()
        self.add_tmp_constraint()
        self.add_linked_sections_constraint()

    def _build_model(self):
        self._add_constraints()

        # take as many courses as possible (temporary testing heuristic)
        self.model.maximize(sum(self.d_vars.course_was_taken.values()))

    def solve(self):
        # need to build after user defined constraints area added

        status = self.solver.solve(self.model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            taken: list[str] = []

            for course_nid, course in self.d_vars.course_was_taken.items():
                if self.solver.value(course) == 1:
                    taken.append(course_nid)

            return TTSolution(
                courses=self.problem_instance.courses,
                courses_taken=taken,
                status=status,
            )
        else:
            return TTSolution(courses=pd.DataFrame(), courses_taken=[], status=status)
