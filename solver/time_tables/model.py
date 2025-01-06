import os
from collections import defaultdict, namedtuple
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from pydantic import BaseModel

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
from solver.v2.util import print_statistics


@dataclass
class TTFilterConstraint:
    course_codes: Optional[list[str]] = None
    subjects: Optional[list[str]] = None
    year_levels: Optional[list[int]] = None

    lte: int = None
    gte: int = None
    eq: int = None


@dataclass
class ForcedConflict:
    day: str
    start: int
    stop: int


class OptimizationTarget(Enum):
    UNKNOWN = 0
    CoursesTaken = 1
    DaysOnCampus = 2
    TimeOnCampus = 3


class TTSolution:
    def __init__(self, courses_taken: list[str], courses: pd.DataFrame, status: any):
        self.courses_taken = courses_taken
        self.courses = courses
        self.status = status

    @property
    def status_ok(self) -> bool:
        if self.status in [
            cp_model.UNKNOWN,
            cp_model.INFEASIBLE,
            cp_model.MODEL_INVALID,
        ]:
            return False
        return True

    def __str__(self):
        buf = ""
        if not self.status_ok:
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

                if len(courses_on_day) == 0:
                    buf += "\tNone\n"

        return buf

    def response(self):
        class Course(BaseModel):
            crn: int
            name: str
            meeting_type: str
            start_time: Optional[int]
            end_time: Optional[int]

        class GenerateResponse(BaseModel):
            courses: dict[str, list[Course]]
            found_solution: bool

        if self.status in [
            cp_model.UNKNOWN,
            cp_model.INFEASIBLE,
            cp_model.MODEL_INVALID,
        ]:
            return GenerateResponse(courses=dict(), found_solution=False)

        res: dict[str, list[Course]] = defaultdict(list)

        for course_nid in self.courses_taken:
            course_info = self.courses.loc[course_nid]
            for meeting_time in course_info["meeting_times"]:
                res[meeting_time.day_of_week()].append(
                    Course(
                        crn=course_info["id"],
                        name=course_info["class_code"],
                        meeting_type=course_info["type"],
                        end_time=meeting_time.end_time,
                        start_time=meeting_time.begin_time,
                    )
                )

        print(res)
        return GenerateResponse(courses=res, found_solution=True)


class TTProblemInstance:
    def __init__(
        self,
        courses: list[MinimumClassInfo],
        forced_conflicts: list[ForcedConflict],
        filter_constraints: list[TTFilterConstraint],
        optimization_target: OptimizationTarget,
    ):

        self.courses = self.__init_courses(courses)
        self.forced_conflicts: list[ForcedConflict] = forced_conflicts
        self.filter_constraints: list[TTFilterConstraint] = filter_constraints
        self.optimization_target = optimization_target

    @staticmethod
    def __init_courses(courses: list[MinimumClassInfo]):
        index = []
        variables = []
        columns = [
            "id",
            "class_code",
            "type",
            "subject",
            "meeting_times",
            "linked_sections",
        ]

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

        print("created conflict", start, end, day)
        self.forced_conflicts.append(ForcedConflict(start=start, stop=end, day=day))

    def add_filter_constraint(
        self, course_names: list[str], subjects: list[str], year_levels: list[int]
    ):
        pass


class TTDependantVariables:
    def __init__(self, model: cp_model.CpModel, courses: pd.DataFrame):
        # meta
        self.__courses = courses
        self.__model = model
        self.courses_on_day = self.__init_courses_on_day()

        # d-vars
        self.course_was_taken: dict[str, cp_model.BoolVarT] = (
            self._init_unknown_variables()
        )
        self.intervals: pd.DataFrame = self._init_interval_variables()

        self.have_courses_on_day: dict[str, cp_model.BoolVarT] = (
            self.__init_have_courses_on_day()
        )

        self.day_starts: dict[str, cp_model.IntVar] = self.__init_day_starts()
        self.day_ends: dict[str, cp_model.IntVar] = self.__init_day_ends()
        self.day_to_time_on_campus: dict[str, cp_model.IntVar] = (
            self.__init_time_on_campus()
        )

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

    def __init_courses_on_day(self) -> dict[str, list[str]]:
        courses_scheduled_on_day: dict[str, list[str]] = defaultdict(list)

        for idx, row in self.__courses.iterrows():
            for mt in row["meeting_times"]:
                if mt.monday:
                    courses_scheduled_on_day["monday"].append(str(idx))
                if mt.tuesday:
                    courses_scheduled_on_day["tuesday"].append(str(idx))
                if mt.wednesday:
                    courses_scheduled_on_day["wednesday"].append(str(idx))
                if mt.thursday:
                    courses_scheduled_on_day["thursday"].append(str(idx))
                if mt.friday:
                    courses_scheduled_on_day["friday"].append(str(idx))

        return courses_scheduled_on_day

    def __init_have_courses_on_day(self) -> dict[str, cp_model.BoolVarT]:
        # if we took a course on that day we're on campus (ignore online courses right now)
        res: dict[str, cp_model.BoolVarT] = dict()

        for day_of_week, courses_running in self.courses_on_day.items():
            class_on_day = self.__model.new_bool_var(f"class_on_{day_of_week}?")

            # 1 if we have any class that day, 0 if no
            self.__model.add_max_equality(
                class_on_day,
                [self.course_was_taken[course_code] for course_code in courses_running],
            )

            res[day_of_week] = class_on_day

        return res

    def __init_day_starts(self):
        # day -> int of its start date
        day_starts: dict[str, cp_model.IntVar] = dict()
        for day, courses in self.courses_on_day.items():
            day_start_var = self.__model.new_int_var(0, 2359, f"{day}_start")

            # if a course isn't taken, say its taken at a really large number
            start_times = []
            for course in courses:
                stv = self.__model.new_int_var(0, 10_000, f"{course}_stv")

                self.__model.add(
                    stv == self.__courses.loc[course]["meeting_times"][0].begin_time
                ).only_enforce_if(self.course_was_taken[course])
                # NOTE: if I make this 10_000 we get valid but bad solutions, not sure why
                self.__model.add(stv == 2359).only_enforce_if(
                    ~self.course_was_taken[course]
                )

                start_times.append(stv)

            # making bad assumptions here but I need to ship
            self.__model.add_min_equality(day_start_var, start_times)

            day_starts[day] = day_start_var

        return day_starts

    def __init_day_ends(self):
        day_ends: dict[str, cp_model.IntVar] = dict()
        for day, courses in self.courses_on_day.items():
            day_end_var = self.__model.new_int_var(0, 2359, f"{day}_end")

            # making bad assumptions here but I need to ship
            self.__model.add_max_equality(
                day_end_var,
                [
                    self.__courses.loc[course]["meeting_times"][0].end_time
                    * self.course_was_taken[course]
                    for course in courses
                ],
            )

            day_ends[day] = day_end_var

        return day_ends

    def __init_time_on_campus(self) -> dict[str, cp_model.IntVar]:
        res = dict()

        for day_of_week in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
            start, end = self.day_starts[day_of_week], self.day_ends[day_of_week]
            time_on_campus_var = self.__model.new_int_var(
                0, 2359, f"{day_of_week}_time_on_campus"
            )

            self.__model.add(time_on_campus_var == end - start).only_enforce_if(
                self.have_courses_on_day[day_of_week]
            )

            self.__model.add(time_on_campus_var == 0).only_enforce_if(
                ~self.have_courses_on_day[day_of_week]
            )

            res[day_of_week] = time_on_campus_var

        return res


class TTSolver:
    def __init__(
        self,
        problem_instance: TTProblemInstance,
        enumerate_all_solutions=None,
    ):
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.problem_instance = problem_instance
        self.enumerate_all_solutions = enumerate_all_solutions

        self.d_vars = TTDependantVariables(
            model=self.model, courses=problem_instance.courses
        )

        self.forced_conflicts: dict[str, list[cp_model.IntervalVar]] = (
            self.__init_forced_conflicts()
        )

        self.callback = Callback(
            courses=self.problem_instance.courses, dvars=self.d_vars
        )

        if enumerate_all_solutions:
            self.solver.parameters.enumerate_all_solutions = True

        # 2.7s -> .12s per solve with this turned on
        self.pre_cull(self.problem_instance.filter_constraints)

        self._build_model()

    def add_no_overlap_constraint(self):
        # we cant take two classes that are scheduled for the same time
        for day in self.d_vars.intervals["day_of_week"].unique():
            course_intervals = self.d_vars.intervals[
                self.d_vars.intervals["day_of_week"] == day
            ]["interval"].values

            forced_conflict_intervals = np.array(self.forced_conflicts[day])
            # print("fci", forced_conflict_intervals)

            all_intervals = np.concatenate(
                (course_intervals, forced_conflict_intervals)
            )

            self.model.add_no_overlap(all_intervals)

    def add_tmp_constraint(self):
        # need to remove though for async online and thesis courses
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
        for fc in self.problem_instance.forced_conflicts:
            _, _, interval_var = create_optional_interval_variable(
                model=self.model,
                start=fc.start,
                end=fc.stop,
                enforce=true_var(self.model),
                name=f"forced_conflict_s{fc.start}_e{fc.stop}_{fc.day}",
            )

            fc_map[fc.day.lower()].append(interval_var)

        return fc_map

    def add_linked_sections_constraint(self):
        course_id_to_course = dict(
            zip(
                self.problem_instance.courses["id"], self.problem_instance.courses.index
            )
        )

        # if a course is taken, one of its linked sections (dnf) must be taken as well
        for course_id, row in self.problem_instance.courses.iterrows():
            if len(row["linked_sections"]) != 0:
                course_taken = self.d_vars.course_was_taken[str(course_id)]

                possible_linked_sections = []
                for linked_section in row["linked_sections"]:
                    linked_sections_taken = [
                        self.d_vars.course_was_taken[course_id_to_course[course_id]]
                        for course_id in linked_section
                    ]

                    possible_linked_sections.append(
                        are_all_true(self.model, linked_sections_taken)
                    )

                # we're not going to take a lab twice, take it once
                self.model.add_at_least_one(possible_linked_sections).only_enforce_if(
                    course_taken
                )
                # self.model.add(sum(possible_linked_sections) == 1).only_enforce_if(
                #     course_taken
                # )

    def collect_filtered_variables(self, f: TTFilterConstraint):
        df = self.problem_instance.courses
        mask = pd.Series(True, index=df.index)

        # only Lectures for now, maybe add CRN filter
        mask &= df["type"] == "Lecture"

        if f.course_codes:
            mask &= df["class_code"].isin(f.course_codes)
        if f.year_levels:
            # TODO: need to add this to min course info scrape
            pass
        if f.subjects:
            mask &= df["subject"].isin(f.subjects)

        course_nids = df[mask].index.tolist()

        res = []
        for course_nid in course_nids:
            res.append(self.d_vars.course_was_taken[course_nid])

        return res

    # TODO: think if i should use this or not
    def pre_cull(self, filters: list[TTFilterConstraint]):
        valid_subjects = set()

        # TODO: year levels
        for f in filters:
            if f.course_codes is not None:
                for cc in f.course_codes:
                    buf = ""
                    pos = 0
                    while not cc[pos].isnumeric():
                        buf += cc[pos]
                        pos += 1

                    valid_subjects.add(buf)
            if f.subjects is not None:
                for subj in f.subjects:
                    valid_subjects.add(subj)

        df = self.problem_instance.courses
        mask = pd.Series(True, index=df.index)
        mask &= ~df["subject"].isin(list(valid_subjects))

        course_nids = df[mask].index.tolist()
        res = []
        for course_nid in course_nids:
            res.append(self.d_vars.course_was_taken[course_nid])

        # user didn't specify these, so we shouldn't take them
        self.model.add(sum(res) == 0)

    def add_filter_constraints(self):
        for fc in self.problem_instance.filter_constraints:
            courses_taken = self.collect_filtered_variables(fc)

            if fc.lte is not None:
                self.model.add(sum(courses_taken) <= fc.lte)

            if fc.gte is not None:
                self.model.add(sum(courses_taken) >= fc.gte)

            if fc.eq is not None:
                self.model.add(sum(courses_taken) == fc.eq)

    def exclude_course(self, course_nid: str):
        assert (
            "_" in course_nid
        ), "course_nid invalid expected format: UNSP1111U_TYPE_CRN"
        course_taken = self.d_vars.course_was_taken[course_nid]
        self.model.add(course_taken == 0)

    def _add_constraints(self):
        self.add_filter_constraints()
        self.add_max_of_course_type_constraint()
        self.add_no_overlap_constraint()
        self.add_tmp_constraint()
        self.add_linked_sections_constraint()

    def _build_model(self):
        self._add_constraints()

        match self.problem_instance.optimization_target:
            case OptimizationTarget.CoursesTaken:
                self.model.minimize(sum(self.d_vars.course_was_taken.values()))
            case OptimizationTarget.DaysOnCampus:
                self.model.minimize(sum(self.d_vars.course_was_taken.values()))
                self.minimize_days_on_campus()
            case OptimizationTarget.TimeOnCampus:
                self.minimize_course_gap()
            case _:
                print("unhandled optimization target")

    def minimize_days_on_campus(self):
        self.model.minimize(sum(self.d_vars.have_courses_on_day.values()))

    def minimize_course_gap(self):
        # time on campus is sort of a proxy for course gap
        self.model.minimize(sum(self.d_vars.day_to_time_on_campus.values()))

    def solve(self) -> TTSolution:
        # status = self.solver.solve(self.model)
        status = -1
        if self.enumerate_all_solutions:
            status = self.solver.solve(self.model, self.callback)
        else:
            status = self.solver.solve(self.model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            if status == cp_model.OPTIMAL:
                print("OPTIMAL")
            taken: list[str] = []

            for course_nid, course in self.d_vars.course_was_taken.items():
                if self.solver.value(course) == 1:
                    taken.append(course_nid)

            print_statistics(self.solver)

            print("On Campus Days:")
            for k, v in self.d_vars.have_courses_on_day.items():
                if self.solver.value(v) == 1:
                    print(k)

            ttoc = 0
            for k, v in self.d_vars.day_starts.items():
                start_var = self.solver.value(self.d_vars.day_starts[k])
                end_var = self.solver.value(self.d_vars.day_ends[k])
                toc = self.solver.value(self.d_vars.day_to_time_on_campus[k])
                ttoc += toc

                print(
                    k,
                    start_var,
                    end_var,
                    toc,
                )

            print("TTOC:", ttoc)

            return TTSolution(
                courses=self.problem_instance.courses,
                courses_taken=taken,
                status=status,
            )
        else:
            return TTSolution(courses=pd.DataFrame(), courses_taken=[], status=status)


class Callback(cp_model.CpSolverSolutionCallback):
    def __init__(self, courses, dvars):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.courses = courses
        self.dvars = dvars
        self.solutions = 0

    def on_solution_callback(self):
        taken: list[str] = []
        self.solutions += 1

        for course_nid, course in self.dvars.course_was_taken.items():
            if self.value(course) == 1:
                taken.append(course_nid)

        sol = TTSolution(
            courses=self.courses, courses_taken=taken, status=cp_model.FEASIBLE
        )

        print("=" * 10, self.solutions, f"({self.objective_value})", "=" * 10)
        print(sol)
