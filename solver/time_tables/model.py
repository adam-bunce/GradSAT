from collections import defaultdict

import numpy as np
import pandas as pd
from ortools.sat.python import cp_model

from scraper.models import MinimumClassInfo
from solver.v2.dependent_variables import (
    false_var,
    zero_int,
    empty_interval,
    are_all_true,
)


class TTSolution:
    def __init__(self, courses_taken: list[str], courses: pd.DataFrame):
        self.courses_taken = courses_taken
        self.courses = courses

    def __str__(self):
        buf = ""
        if len(self.courses_taken) == 0:
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
        self, courses: list[MinimumClassInfo], forced_conflicts: list[tuple[int, int]]
    ):

        self.courses = self.__init_courses(courses)
        self.forced_conflicts = forced_conflicts  # blacklisted time boxes

    @staticmethod
    def __init_courses(courses: list[MinimumClassInfo]):
        index = []
        variables = []
        columns = ["id", "class_code", "type", "meeting_times", "linked_sections"]

        for course in courses:
            variables.append([getattr(course, col) for col in columns])
            index.append(course.info_id())

        return pd.DataFrame(variables, index=index, columns=columns)


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

                    start = self.__model.new_int_var(
                        lb=meeting_time.begin_time,
                        ub=meeting_time.begin_time,
                        name=f"{row.iloc[0]}_start_{j}",
                    )

                    end = self.__model.new_int_var(
                        lb=meeting_time.end_time,
                        ub=meeting_time.end_time,
                        name=f"{row.iloc[0]}_end_{j}",
                    )

                    # duration doesn't matter in this case b/c end/start don't get set, we just use it to invalidate possible classes
                    duration = meeting_time.end_time - meeting_time.begin_time

                    # curr_course_was_taken[]
                    curr_course_was_taken = self.course_was_taken[row_index]

                    interval = self.__model.new_optional_interval_var(
                        start=start,
                        end=end,
                        size=duration,
                        is_present=curr_course_was_taken,
                        name=f"{row.iloc[0]}_interval_{j}",
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

        self._build_model()

    def add_no_overlap_constraint(self):
        # we cant take two classes that are scheduled for the same time
        for day in self.d_vars.intervals["day_of_week"].unique():
            intervals = self.d_vars.intervals[
                self.d_vars.intervals["day_of_week"] == day
            ]["interval"].values

            self.model.add_no_overlap(intervals)

    def add_tmp_constraint(self):
        # tmp constraint to ignore courses with no scheduling (sanity checks are easier)
        for course in self.problem_instance.courses.index:
            curr_course_was_taken = self.d_vars.course_was_taken[course]

            if len(self.problem_instance.courses.loc[course]["meeting_times"]) == 0:
                self.model.add(curr_course_was_taken == 0)

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
        self.add_no_overlap_constraint()
        self.add_tmp_constraint()
        self.add_linked_sections_constraint()

    def _build_model(self):
        self._add_constraints()

        # take as many courses as possible (temporary testing heuristic)
        self.model.maximize(sum(self.d_vars.course_was_taken.values()))

    def solve(self):
        status = self.solver.solve(self.model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            taken: list[str] = []

            for course_nid, course in self.d_vars.course_was_taken.items():
                if self.solver.value(course) == 1:
                    taken.append(course_nid)

            return TTSolution(
                courses=self.problem_instance.courses, courses_taken=taken
            )
        else:
            return (TTSolution(courses=pd.DataFrame(), courses_taken=[]),)
